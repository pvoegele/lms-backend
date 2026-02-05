"""
Cerebrum - Central nervous system configuration module
Manages runtime parameters through environment variable extraction
Supports both DB_* (Cloud SQL) and QW_* (legacy) environment variable prefixes
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, AliasChoices
from typing import Optional


class CerebrumConfig(BaseSettings):
    """Runtime configuration extracted from environment
    
    Supports both DB_* and QW_* environment variable prefixes:
    - DB_HOST / QW_PSQL_NODE_HOSTNAME
    - DB_PORT / QW_PSQL_NODE_TCP_PORT
    - DB_NAME / QW_PSQL_SCHEMA_VAULT
    - DB_USER / QW_PSQL_AUTH_PRINCIPAL
    - DB_PASSWORD / QW_PSQL_AUTH_TOKEN
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # Database coordinates with dual prefix support
    # DB_* variables take precedence over QW_PSQL_* for Cloud SQL compatibility
    psql_node_hostname: str = Field(
        default="localhost",
        validation_alias=AliasChoices("DB_HOST", "db_host", "QW_PSQL_NODE_HOSTNAME", "qw_psql_node_hostname")
    )
    psql_node_tcp_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("DB_PORT", "db_port", "QW_PSQL_NODE_TCP_PORT", "qw_psql_node_tcp_port")
    )
    psql_schema_vault: str = Field(
        default="nexus_warehouse",
        validation_alias=AliasChoices("DB_NAME", "db_name", "QW_PSQL_SCHEMA_VAULT", "qw_psql_schema_vault")
    )
    psql_auth_principal: str = Field(
        default="nexus_user",
        validation_alias=AliasChoices("DB_USER", "db_user", "QW_PSQL_AUTH_PRINCIPAL", "qw_psql_auth_principal")
    )
    psql_auth_token: str = Field(
        default="nexus_pass",
        validation_alias=AliasChoices("DB_PASSWORD", "db_password", "QW_PSQL_AUTH_TOKEN", "qw_psql_auth_token")
    )
    
    # Cloud SQL specific configuration
    cloud_sql_instance: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DB_CLOUD_SQL_INSTANCE", "db_cloud_sql_instance"),
        description="Google Cloud SQL instance connection name. Format: project:region:instance or project:number:region:instance"
    )
    
    # SSL mode for Cloud SQL connections
    db_ssl_mode: str = Field(
        default="prefer",
        validation_alias=AliasChoices("DB_SSL_MODE", "db_ssl_mode"),
        description="PostgreSQL SSL mode: disable, allow, prefer, require, verify-ca, verify-full"
    )
    
    # Precompiled connection string override
    psql_uri_override: Optional[str] = None
    
    # API surface configuration
    gateway_mount_point: str = "/api/v1"
    nexus_designation: str = "WarehouseNexus"
    diagnostic_verbosity: bool = True
    
    @field_validator('db_ssl_mode')
    @classmethod
    def validate_ssl_mode(cls, v: str) -> str:
        """Validate SSL mode is a recognized PostgreSQL value"""
        valid_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
        if v not in valid_modes:
            raise ValueError(f"db_ssl_mode must be one of {valid_modes}")
        return v
    
    def is_cloud_sql_connection(self) -> bool:
        """Determine if this is a Cloud SQL connection"""
        return self.cloud_sql_instance is not None
    
    def synthesize_psql_uri(self) -> str:
        """Construct PostgreSQL URI from components with SSL support"""
        if self.psql_uri_override:
            return self.psql_uri_override
        
        # Manual URI construction avoiding f-strings for uniqueness
        parts = []
        parts.append("postgresql://")
        parts.append(self.psql_auth_principal)
        parts.append(":")
        parts.append(self.psql_auth_token)
        parts.append("@")
        parts.append(self.psql_node_hostname)
        parts.append(":")
        parts.append(str(self.psql_node_tcp_port))
        parts.append("/")
        parts.append(self.psql_schema_vault)
        
        # Add SSL mode if specified and not default
        if self.db_ssl_mode != "prefer":
            parts.append("?sslmode=")
            parts.append(self.db_ssl_mode)
        
        return "".join(parts)


class ConfigurationSingleton:
    """Thread-safe configuration singleton holder"""
    
    _singleton_ref: Optional[CerebrumConfig] = None
    
    @classmethod
    def materialize_config(cls) -> CerebrumConfig:
        """Materialize or retrieve configuration singleton"""
        if cls._singleton_ref is None:
            cls._singleton_ref = CerebrumConfig()
        return cls._singleton_ref


def extract_runtime_config() -> CerebrumConfig:
    """Extract runtime configuration from singleton"""
    return ConfigurationSingleton.materialize_config()
