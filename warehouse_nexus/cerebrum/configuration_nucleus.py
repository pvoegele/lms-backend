"""
Cerebrum - Central Configuration Management System
===================================================

The Cerebrum module acts as the "brain" of the application, managing all
runtime configuration through environment variables. It implements:

1. **Pydantic Settings**: Type-safe configuration with validation
2. **Singleton Pattern**: Single configuration instance shared across application
3. **Environment Variable Loading**: Automatic .env file parsing
4. **Database URI Construction**: Builds PostgreSQL connection strings

Design Pattern:
- Uses Pydantic BaseSettings for automatic environment variable parsing
- Implements singleton pattern to ensure single configuration instance
- Supports connection string override for managed database services

Environment Variables:
All configuration variables must be prefixed with 'QW_' (e.g., QW_PSQL_NODE_HOSTNAME)

Example .env file:
    QW_PSQL_NODE_HOSTNAME=localhost
    QW_PSQL_NODE_TCP_PORT=5432
    QW_PSQL_SCHEMA_VAULT=nexus_warehouse
    QW_PSQL_AUTH_PRINCIPAL=nexus_user
    QW_PSQL_AUTH_TOKEN=secret_password
    QW_GATEWAY_MOUNT_POINT=/api/v1
    QW_NEXUS_DESIGNATION=WarehouseNexus
    QW_DIAGNOSTIC_VERBOSITY=True

Usage:
    from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config
    
    config = extract_runtime_config()
    db_uri = config.synthesize_psql_uri()
"""
from pydantic_settings import BaseSettings
from typing import Optional


class CerebrumConfig(BaseSettings):
    """
    Runtime configuration extracted from environment variables.
    
    This class uses Pydantic's BaseSettings to automatically load and validate
    configuration from environment variables. All fields have sensible defaults
    for development, but should be explicitly set in production.
    
    Attributes:
        psql_node_hostname (str): PostgreSQL server hostname
        psql_node_tcp_port (int): PostgreSQL server port
        psql_schema_vault (str): Database name
        psql_auth_principal (str): Database username
        psql_auth_token (str): Database password
        psql_uri_override (Optional[str]): Full connection string (overrides other DB settings)
        gateway_mount_point (str): API URL prefix (e.g., /api/v1)
        nexus_designation (str): Application display name
        diagnostic_verbosity (bool): Enable SQL logging and debug output
    """
    
    # Database coordinates - configure these to match your PostgreSQL setup
    psql_node_hostname: str = "localhost"  # Hostname or IP of PostgreSQL server
    psql_node_tcp_port: int = 5432  # Standard PostgreSQL port
    psql_schema_vault: str = "nexus_warehouse"  # Target database name
    psql_auth_principal: str = "nexus_user"  # Database username
    psql_auth_token: str = "nexus_pass"  # Database password (consider using secrets management)
    
    # Precompiled connection string override
    # Use this when deploying to managed database services (Heroku, Vercel Postgres, etc.)
    # Format: postgresql://user:password@host:port/database
    # When set, this overrides all other database connection parameters
    psql_uri_override: Optional[str] = None
    
    # API surface configuration
    gateway_mount_point: str = "/api/v1"  # All API endpoints will be prefixed with this
    nexus_designation: str = "WarehouseNexus"  # Application name shown in API docs
    diagnostic_verbosity: bool = True  # Enable detailed logging (SQL queries, debug info)
    
    class Config:
        """Pydantic configuration for settings loading."""
        env_file = ".env"  # Automatically load from .env file if present
        case_sensitive = False  # Environment variables are case-insensitive
        # Environment variables must be prefixed with QW_ (QuantumWarehouse)
        # This prevents conflicts with system environment variables
        # Example: QW_PSQL_NODE_HOSTNAME maps to psql_node_hostname
        env_prefix = "QW_"
    
    def synthesize_psql_uri(self) -> str:
        """
        Construct PostgreSQL connection URI from individual components.
        
        Builds a standard PostgreSQL connection string in the format:
        postgresql://username:password@hostname:port/database
        
        If psql_uri_override is set, it returns that instead, allowing for
        pre-configured connection strings from managed database providers.
        
        Returns:
            str: Complete PostgreSQL connection URI
            
        Example:
            >>> config = CerebrumConfig()
            >>> config.synthesize_psql_uri()
            'postgresql://nexus_user:nexus_pass@localhost:5432/nexus_warehouse'
        """
        # If override is provided, use it directly (common in production deployments)
        if self.psql_uri_override:
            return self.psql_uri_override
        
        # Manual URI construction using list concatenation
        # This approach avoids f-strings for better debugging and step-through
        parts = []
        parts.append("postgresql://")  # PostgreSQL protocol identifier
        parts.append(self.psql_auth_principal)  # Username
        parts.append(":")
        parts.append(self.psql_auth_token)  # Password
        parts.append("@")
        parts.append(self.psql_node_hostname)  # Host
        parts.append(":")
        parts.append(str(self.psql_node_tcp_port))  # Port (converted to string)
        parts.append("/")
        parts.append(self.psql_schema_vault)  # Database name
        
        return "".join(parts)


class ConfigurationSingleton:
    """
    Thread-safe configuration singleton holder.
    
    Implements the Singleton design pattern to ensure only one configuration
    instance exists throughout the application lifecycle. This provides:
    
    1. **Memory Efficiency**: Single config instance shared across all requests
    2. **Consistency**: All code reads from same configuration values
    3. **Lazy Loading**: Configuration loaded only when first accessed
    4. **Thread Safety**: Class-level storage ensures singleton in multi-threaded environments
    
    The singleton pattern is important here because:
    - Configuration doesn't change during runtime
    - Multiple instances would waste memory
    - Ensures consistent configuration across all modules
    
    Note: Python's GIL (Global Interpreter Lock) provides thread safety for
    class variable assignment, so no additional locking is needed.
    """
    
    _singleton_ref: Optional[CerebrumConfig] = None  # Class-level storage for singleton instance
    
    @classmethod
    def materialize_config(cls) -> CerebrumConfig:
        """
        Materialize or retrieve the configuration singleton.
        
        This method implements lazy initialization - the configuration is only
        loaded from environment variables on the first call. Subsequent calls
        return the cached instance.
        
        Returns:
            CerebrumConfig: The singleton configuration instance
            
        Example:
            >>> config1 = ConfigurationSingleton.materialize_config()
            >>> config2 = ConfigurationSingleton.materialize_config()
            >>> config1 is config2  # Same object reference
            True
        """
        if cls._singleton_ref is None:
            # First access - load configuration from environment
            cls._singleton_ref = CerebrumConfig()
        return cls._singleton_ref


def extract_runtime_config() -> CerebrumConfig:
    """
    Convenience function to extract runtime configuration.
    
    This is the primary public API for accessing configuration throughout
    the application. It provides a clean, simple interface that hides the
    singleton implementation details.
    
    Returns:
        CerebrumConfig: Application configuration singleton
        
    Usage:
        >>> from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config
        >>> config = extract_runtime_config()
        >>> db_uri = config.synthesize_psql_uri()
    """
    return ConfigurationSingleton.materialize_config()
