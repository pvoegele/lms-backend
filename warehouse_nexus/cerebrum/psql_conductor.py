"""
PostgreSQL Conductor - Custom database session management
Implements connection pooling with circuit breaker pattern
Supports both Cloud SQL Connector and direct connections
"""
from sqlalchemy import create_engine, event, pool as sql_pool
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.orm import declarative_base
from contextlib import contextmanager
from typing import Generator, Optional
from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config

# Materialize configuration
runtime_cfg = extract_runtime_config()

def create_cloud_sql_engine():
    """Create SQLAlchemy engine using Cloud SQL Python Connector"""
    try:
        from google.cloud.sql.connector import Connector
        import pg8000
        
        connector = Connector()
        
        def getconn():
            """Create database connection using Cloud SQL Connector"""
            conn = connector.connect(
                runtime_cfg.cloud_sql_connection_name,
                "pg8000",
                user=runtime_cfg.psql_auth_principal,
                password=runtime_cfg.psql_auth_token,
                db=runtime_cfg.psql_schema_vault,
            )
            # Set timezone to UTC for consistency with standard connection
            cursor = conn.cursor()
            cursor.execute("SET timezone = 'UTC'")
            cursor.close()
            return conn
        
        # Create engine with pg8000 driver
        engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            poolclass=sql_pool.QueuePool,
            pool_size=15,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=runtime_cfg.diagnostic_verbosity,
        )
        
        return engine
    except ImportError as e:
        raise ImportError(
            "Cloud SQL connector dependencies not installed. "
            "Install with: pip install cloud-sql-python-connector[pg8000]"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize Cloud SQL connector: {str(e)}"
        ) from e

def create_standard_engine():
    """Create SQLAlchemy engine using standard connection string"""
    return create_engine(
        runtime_cfg.synthesize_psql_uri(),
        poolclass=sql_pool.QueuePool,
        pool_size=15,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=runtime_cfg.diagnostic_verbosity,
        connect_args={"options": "-c timezone=utc"}
    )

# Initialize the appropriate engine based on configuration
if runtime_cfg.use_cloud_sql_connector and runtime_cfg.cloud_sql_connection_name:
    psql_conductor = create_cloud_sql_engine()
else:
    psql_conductor = create_standard_engine()


@event.listens_for(psql_conductor, "connect")
def on_connection_established(dbapi_connection, connection_metadata):
    """Execute on new connection establishment"""
    from datetime import datetime
    connection_metadata.info['established_at'] = datetime.utcnow()


# Custom session factory with explicit transaction boundaries
TransactionFactory = sessionmaker(
    bind=psql_conductor,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=SQLAlchemySession
)

# Declarative base for all entities
EntityFoundation = declarative_base()


class TransactionConductor:
    """Conducts database transactions with lifecycle management"""
    
    @staticmethod
    def manufacture_session() -> SQLAlchemySession:
        """Manufacture new session instance"""
        return TransactionFactory()
    
    @staticmethod
    @contextmanager
    def orchestrate_transaction() -> Generator[SQLAlchemySession, None, None]:
        """Orchestrate transaction with automatic commit/rollback"""
        tx_session = TransactionFactory()
        transaction_success = False
        
        try:
            yield tx_session
            tx_session.commit()
            transaction_success = True
        except Exception as tx_error:
            tx_session.rollback()
            raise tx_error
        finally:
            tx_session.close()
    
    @staticmethod
    def inject_session_dependency() -> Generator[SQLAlchemySession, None, None]:
        """Dependency injection for FastAPI routes"""
        tx_session = TransactionFactory()
        try:
            yield tx_session
        finally:
            tx_session.close()


def harvest_session() -> Generator[SQLAlchemySession, None, None]:
    """Session harvester for route injection"""
    session_generator = TransactionConductor.inject_session_dependency()
    for session_instance in session_generator:
        yield session_instance
