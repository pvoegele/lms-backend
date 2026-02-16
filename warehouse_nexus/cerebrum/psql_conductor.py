"""
PostgreSQL Conductor - Database Session and Connection Management
=================================================================

This module manages database connectivity and session lifecycle for the entire application.
It implements several important patterns:

1. **Connection Pooling**: Maintains a pool of database connections for efficiency
2. **Session Management**: Provides context managers for transaction handling
3. **Circuit Breaker Awareness**: Pool configuration prevents connection exhaustion
4. **Dependency Injection**: Seamless integration with FastAPI's dependency system

Key Components:
- psql_conductor: SQLAlchemy engine with connection pool
- TransactionFactory: Session factory for creating new sessions
- EntityFoundation: Base class for all ORM models
- TransactionConductor: Helper class for transaction management
- harvest_session(): FastAPI dependency for route injection

Connection Pool Configuration:
- Base pool size: 15 connections (steady-state workload)
- Max overflow: 30 additional connections (burst capacity)
- Pool pre-ping: Validates connections before use (handles stale connections)
- Pool recycle: Connections recycled every 30 minutes (prevents stale sessions)
- Timezone: UTC enforced for consistent datetime handling

Usage in FastAPI Routes:
    from warehouse_nexus.cerebrum.psql_conductor import harvest_session
    
    @app.get("/items")
    def get_items(db: Session = Depends(harvest_session)):
        # db is automatically injected and closed after request
        items = db.query(Item).all()
        return items

Usage for Manual Transactions:
    from warehouse_nexus.cerebrum.psql_conductor import TransactionConductor
    
    with TransactionConductor.orchestrate_transaction() as session:
        # Operations here
        session.add(new_item)
        # Automatically commits on success, rolls back on exception
"""
from sqlalchemy import create_engine, event, pool as sql_pool
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.orm import declarative_base
from contextlib import contextmanager
from typing import Generator, Optional
from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config

# Materialize configuration singleton
# This is loaded once when the module is imported
runtime_cfg = extract_runtime_config()

# Custom engine with production-ready connection pool configuration
# The engine is the heart of SQLAlchemy's database connectivity
psql_conductor = create_engine(
    runtime_cfg.synthesize_psql_uri(),  # PostgreSQL connection string
    poolclass=sql_pool.QueuePool,  # Queue-based connection pool (thread-safe)
    pool_size=15,  # Base number of connections maintained in pool
    max_overflow=30,  # Additional connections created under load (total: 45)
    pool_pre_ping=True,  # Test connection health before using (catches dropped connections)
    pool_recycle=1800,  # Recycle connections after 30 minutes (prevents stale connections)
    echo=runtime_cfg.diagnostic_verbosity,  # Log all SQL when diagnostics enabled
    connect_args={"options": "-c timezone=utc"}  # Force UTC timezone for consistency
    # Why UTC? Avoids timezone-related bugs, standard practice for distributed systems
)


# Event listener for connection establishment
# This hook is called every time a new connection is created
@event.listens_for(psql_conductor, "connect")
def on_connection_established(dbapi_connection, connection_metadata):
    """
    Event handler triggered when a new database connection is established.
    
    This function is called by SQLAlchemy each time a new physical database
    connection is created (not just retrieved from the pool). It can be used to:
    - Record connection metrics
    - Set connection-specific parameters
    - Log connection events
    - Initialize connection state
    
    Args:
        dbapi_connection: The raw DBAPI connection object (psycopg2 connection)
        connection_metadata: SQLAlchemy metadata dictionary for storing connection info
        
    Note:
        This is NOT called when reusing a pooled connection, only on new connections.
    """
    from datetime import datetime
    # Store connection timestamp in metadata for debugging/monitoring
    connection_metadata.info['established_at'] = datetime.utcnow()
    # Additional operations could include:
    # - Setting statement timeout
    # - Configuring search path
    # - Loading extensions


# Custom session factory with explicit transaction boundaries
# SessionMaker is a factory that produces new Session objects
TransactionFactory = sessionmaker(
    bind=psql_conductor,  # Bind to our engine
    autocommit=False,  # Explicit commit required (ACID compliance)
    autoflush=False,  # Manual flushing for better control
    expire_on_commit=False,  # Keep objects usable after commit (important for FastAPI)
    class_=SQLAlchemySession  # Use standard SQLAlchemy Session class
)
# Why these settings?
# - autocommit=False: Explicit transactions prevent accidental data corruption
# - autoflush=False: Manual control over when SQL is sent to database
# - expire_on_commit=False: Objects remain accessible after commit (crucial for API responses)

# Declarative base for all ORM entity definitions
# All database models must inherit from this base class
EntityFoundation = declarative_base()
# Usage example:
# class Product(EntityFoundation):
#     __tablename__ = 'product'
#     product_id = Column(UUID, primary_key=True)


class TransactionConductor:
    """
    Conducts database transactions with comprehensive lifecycle management.
    
    This class provides three patterns for database session management:
    
    1. **manufacture_session()**: Create a session manually (caller manages lifecycle)
    2. **orchestrate_transaction()**: Context manager with automatic commit/rollback
    3. **inject_session_dependency()**: FastAPI dependency injection pattern
    
    The class uses static methods since it doesn't maintain instance state,
    acting as a namespace for related transaction management functions.
    
    Examples:
        # Pattern 1: Manual session management
        >>> session = TransactionConductor.manufacture_session()
        >>> try:
        >>>     session.add(item)
        >>>     session.commit()
        >>> except:
        >>>     session.rollback()
        >>> finally:
        >>>     session.close()
        
        # Pattern 2: Context manager (recommended for scripts)
        >>> with TransactionConductor.orchestrate_transaction() as session:
        >>>     session.add(item)
        >>>     # Auto-commits on success, rolls back on exception
        
        # Pattern 3: FastAPI dependency (recommended for APIs)
        >>> @app.get("/items")
        >>> def get_items(db: Session = Depends(harvest_session)):
        >>>     return db.query(Item).all()
    """
    
    @staticmethod
    def manufacture_session() -> SQLAlchemySession:
        """
        Manufacture a new database session instance.
        
        Creates a new session using the TransactionFactory. The caller is
        responsible for managing the session lifecycle (commit, rollback, close).
        
        Use this when you need fine-grained control over transaction boundaries,
        such as in complex business logic with multiple decision points.
        
        Returns:
            SQLAlchemySession: New database session instance
            
        Warning:
            Always close the session when done to prevent connection leaks!
        """
        return TransactionFactory()
    
    @staticmethod
    @contextmanager
    def orchestrate_transaction() -> Generator[SQLAlchemySession, None, None]:
        """
        Orchestrate a database transaction with automatic commit/rollback.
        
        This context manager implements the Unit of Work pattern:
        - Creates a new session
        - Yields it for use
        - Commits on success
        - Rolls back on exception
        - Always closes the session
        
        The transaction is only committed if no exception occurs. Any exception
        triggers a rollback, ensuring data consistency.
        
        Yields:
            SQLAlchemySession: Database session for transaction operations
            
        Raises:
            Exception: Any exception raised within the context is re-raised
                      after rollback
                      
        Example:
            >>> with TransactionConductor.orchestrate_transaction() as session:
            >>>     product = session.query(Product).first()
            >>>     product.price = 99.99
            >>>     # Automatically committed here if no exception
        """
        tx_session = TransactionFactory()
        transaction_success = False
        
        try:
            yield tx_session  # Provide session to caller
            tx_session.commit()  # Commit if no exception raised
            transaction_success = True
        except Exception as tx_error:
            tx_session.rollback()  # Rollback on any exception
            raise tx_error  # Re-raise for caller to handle
        finally:
            tx_session.close()  # Always release connection back to pool
    
    @staticmethod
    def inject_session_dependency() -> Generator[SQLAlchemySession, None, None]:
        """
        Dependency injection helper for FastAPI routes.
        
        This generator creates a session and ensures it's closed after use.
        Designed specifically for FastAPI's dependency injection system.
        
        Unlike orchestrate_transaction(), this does NOT auto-commit. The route
        handler is responsible for committing or rolling back as needed.
        
        Yields:
            SQLAlchemySession: Database session for route handler
            
        Usage in FastAPI:
            >>> from fastapi import Depends
            >>> 
            >>> @app.post("/items")
            >>> def create_item(
            >>>     item: ItemCreate,
            >>>     db: Session = Depends(harvest_session)
            >>> ):
            >>>     new_item = Item(**item.dict())
            >>>     db.add(new_item)
            >>>     db.commit()  # Explicit commit required
            >>>     return new_item
        """
        tx_session = TransactionFactory()
        try:
            yield tx_session  # FastAPI injects this into route handler
        finally:
            tx_session.close()  # Always cleanup after request completes


def harvest_session() -> Generator[SQLAlchemySession, None, None]:
    """
    Session harvester for FastAPI route dependency injection.
    
    This is the primary public API for getting database sessions in FastAPI routes.
    It wraps TransactionConductor.inject_session_dependency() to provide a clean,
    simple interface.
    
    The function is a generator that yields a database session, which FastAPI
    automatically injects into route handlers through the Depends() mechanism.
    
    Yields:
        SQLAlchemySession: Database session for route handler use
        
    Usage:
        >>> from warehouse_nexus.cerebrum.psql_conductor import harvest_session
        >>> from fastapi import Depends
        >>> 
        >>> @router.get("/products")
        >>> def list_products(
        >>>     skip: int = 0,
        >>>     limit: int = 100,
        >>>     db: Session = Depends(harvest_session)  # Session automatically injected
        >>> ):
        >>>     products = db.query(Product).offset(skip).limit(limit).all()
        >>>     return products
        
    Note:
        The session is automatically closed after the response is sent,
        even if an exception occurs during request processing.
    """
    session_generator = TransactionConductor.inject_session_dependency()
    for session_instance in session_generator:
        yield session_instance
