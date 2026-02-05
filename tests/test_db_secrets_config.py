"""
Test DB_ secrets configuration support
Validates that both DB_* and QW_* environment variables work correctly
"""
import os
import pytest
from unittest.mock import patch


def test_db_prefix_variables_override_qw_prefix():
    """Test that DB_* variables take precedence over QW_* variables"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {
        'DB_HOST': '34.40.117.250',
        'DB_PORT': '5432',
        'DB_NAME': 'cloud_db',
        'DB_USER': 'cloud_user',
        'DB_PASSWORD': 'cloud_pass',
        'DB_SSL_MODE': 'require',
        'QW_PSQL_NODE_HOSTNAME': 'localhost',
        'QW_PSQL_NODE_TCP_PORT': '5433',
    }, clear=False):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        # DB_* variables should take precedence
        assert config.psql_node_hostname == '34.40.117.250'
        assert config.psql_node_tcp_port == 5432
        assert config.psql_schema_vault == 'cloud_db'
        assert config.psql_auth_principal == 'cloud_user'
        assert config.psql_auth_token == 'cloud_pass'
        assert config.db_ssl_mode == 'require'


def test_qw_prefix_fallback():
    """Test that QW_* variables work when DB_* variables are not set"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {
        'QW_PSQL_NODE_HOSTNAME': 'legacy_host',
        'QW_PSQL_NODE_TCP_PORT': '5433',
        'QW_PSQL_SCHEMA_VAULT': 'legacy_db',
        'QW_PSQL_AUTH_PRINCIPAL': 'legacy_user',
        'QW_PSQL_AUTH_TOKEN': 'legacy_pass',
    }, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        # QW_* variables should be used
        assert config.psql_node_hostname == 'legacy_host'
        assert config.psql_node_tcp_port == 5433
        assert config.psql_schema_vault == 'legacy_db'
        assert config.psql_auth_principal == 'legacy_user'
        assert config.psql_auth_token == 'legacy_pass'


def test_default_values():
    """Test that default values are used when no environment variables are set"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {}, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        # Default values should be used
        assert config.psql_node_hostname == 'localhost'
        assert config.psql_node_tcp_port == 5432
        assert config.psql_schema_vault == 'nexus_warehouse'
        assert config.psql_auth_principal == 'nexus_user'
        assert config.psql_auth_token == 'nexus_pass'
        assert config.db_ssl_mode == 'prefer'


def test_ssl_mode_validation():
    """Test that SSL mode validation works correctly"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {'DB_SSL_MODE': 'invalid_mode'}, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            config = CerebrumConfig()


def test_ssl_mode_in_uri():
    """Test that SSL mode is included in synthesized URI when not default"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {
        'DB_HOST': '34.40.117.250',
        'DB_PORT': '5432',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_pass',
        'DB_SSL_MODE': 'require',
    }, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        uri = config.synthesize_psql_uri()
        assert 'sslmode=require' in uri
        assert '34.40.117.250' in uri


def test_ssl_mode_not_in_uri_when_default():
    """Test that SSL mode is not included in URI when using default 'prefer'"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_pass',
    }, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        uri = config.synthesize_psql_uri()
        assert 'sslmode' not in uri


def test_cloud_sql_instance_field():
    """Test that cloud_sql_instance field is correctly set"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {
        'DB_CLOUD_SQL_INSTANCE': 'cogent-quarter-486519:13:europe-west3:lms-backend-db',
    }, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        assert config.cloud_sql_instance == 'cogent-quarter-486519:13:europe-west3:lms-backend-db'
        assert config.is_cloud_sql_connection() is True


def test_is_cloud_sql_connection():
    """Test the is_cloud_sql_connection helper method"""
    # Reset the singleton before test
    from warehouse_nexus.cerebrum.configuration_nucleus import ConfigurationSingleton
    ConfigurationSingleton._singleton_ref = None
    
    with patch.dict(os.environ, {}, clear=True):
        from warehouse_nexus.cerebrum.configuration_nucleus import CerebrumConfig
        config = CerebrumConfig()
        
        assert config.is_cloud_sql_connection() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
