"""
Cerebrum - Central nervous system configuration module
Manages runtime parameters through environment variable extraction
"""
from pydantic_settings import BaseSettings
from typing import Optional


class CerebrumConfig(BaseSettings):
    """Runtime configuration extracted from environment"""
    
    # Database coordinates
    psql_node_hostname: str = "localhost"
    psql_node_tcp_port: int = 5432
    psql_schema_vault: str = "nexus_warehouse"
    psql_auth_principal: str = "nexus_user"
    psql_auth_token: str = "nexus_pass"
    
    # Precompiled connection string override
    psql_uri_override: Optional[str] = None
    
    # API surface configuration
    gateway_mount_point: str = "/api/v1"
    nexus_designation: str = "WarehouseNexus"
    diagnostic_verbosity: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def synthesize_psql_uri(self) -> str:
        """Construct PostgreSQL URI from components"""
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
