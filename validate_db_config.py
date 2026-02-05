#!/usr/bin/env python
"""
Database Connection Validation Script
Tests the database connection configuration without starting the full application
"""

import sys
import os
from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config

def validate_configuration():
    """Validate database configuration and display connection details"""
    try:
        print("=" * 60)
        print("Database Configuration Validation")
        print("=" * 60)
        
        config = extract_runtime_config()
        
        print("\n📋 Configuration loaded successfully!")
        print("\n🔧 Database Settings:")
        print(f"   Host: {config.psql_node_hostname}")
        print(f"   Port: {config.psql_node_tcp_port}")
        print(f"   Database: {config.psql_schema_vault}")
        print(f"   User: {config.psql_auth_principal}")
        print(f"   SSL Mode: {config.db_ssl_mode}")
        
        if config.cloud_sql_instance:
            print(f"   Cloud SQL Instance: {config.cloud_sql_instance}")
            print("   ✅ Cloud SQL configuration detected")
        
        print("\n🔗 Connection URI:")
        # Mask password in output
        uri = config.synthesize_psql_uri()
        masked_uri = uri.replace(config.psql_auth_token, "***")
        print(f"   {masked_uri}")
        
        print("\n📊 API Configuration:")
        print(f"   Mount Point: {config.gateway_mount_point}")
        print(f"   Designation: {config.nexus_designation}")
        print(f"   Verbose Logging: {config.diagnostic_verbosity}")
        
        # Determine configuration source
        print("\n📌 Configuration Source:")
        db_host_env = os.environ.get('DB_HOST')
        qw_host_env = os.environ.get('QW_PSQL_NODE_HOSTNAME')
        
        if db_host_env:
            print("   Using DB_* environment variables (Google Cloud SQL mode)")
        elif qw_host_env:
            print("   Using QW_* environment variables (Legacy mode)")
        else:
            print("   Using default configuration values")
        
        print("\n" + "=" * 60)
        print("✅ Configuration validation successful!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Configuration validation failed!")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print("\nPlease check your .env file or environment variables.")
        return False


def test_database_connection():
    """Test actual database connection"""
    try:
        print("\n🔌 Testing database connection...")
        from warehouse_nexus.cerebrum.psql_conductor import psql_conductor
        
        with psql_conductor.connect() as connection:
            result = connection.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"   ✅ Connection successful!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            return True
            
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        print("\n   Possible issues:")
        print("   - Database server is not running")
        print("   - Incorrect host/port configuration")
        print("   - Invalid credentials")
        print("   - Network connectivity issues")
        print("   - Database does not exist")
        return False


if __name__ == "__main__":
    config_valid = validate_configuration()
    
    if config_valid:
        print("\n" + "=" * 60)
        user_input = input("\nTest database connection? (y/N): ").strip().lower()
        if user_input == 'y':
            connection_valid = test_database_connection()
            sys.exit(0 if connection_valid else 1)
        else:
            print("Skipping connection test.")
            sys.exit(0)
    else:
        sys.exit(1)
