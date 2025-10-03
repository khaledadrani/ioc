#!/usr/bin/env python3
"""Configuration provider examples."""

import os
import tempfile
import json
from ioc.config_provider import ConfigurationProvider
from ioc.providers import FactoryProvider, SingletonProvider
from ioc.container import BaseContainer
from tests.conftest import DummyDatabase, DummyRepository, DummyService


def test_basic_configuration():
    print("=== Testing Basic Configuration ===")
    
    # Create configuration
    config = ConfigurationProvider()
    config.from_dict({
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "myapp"
        },
        "debug": True,
        "timeout": 30
    })
    
    # Access configuration values
    print(f"✓ Database host: {config.database.host()}")
    print(f"✓ Database port: {config.database.port()}")
    print(f"✓ Debug mode: {config.debug()}")
    print(f"✓ Full config: {config()}")


def test_typed_configuration():
    print("\n=== Testing Typed Configuration ===")
    
    config = ConfigurationProvider()
    config.from_dict({
        "database": {
            "port": "5432",
            "timeout": "30.5",
            "ssl": "true"
        }
    })
    
    # Type conversion
    port = config.database.port.as_int()()
    timeout = config.database.timeout.as_float()()
    ssl_enabled = config.database.ssl.as_bool()()
    
    print(f"✓ Port as int: {port} (type: {type(port).__name__})")
    print(f"✓ Timeout as float: {timeout} (type: {type(timeout).__name__})")
    print(f"✓ SSL as bool: {ssl_enabled} (type: {type(ssl_enabled).__name__})")


def test_json_configuration():
    print("\n=== Testing JSON Configuration ===")
    
    # Create temporary JSON file
    config_data = {
        "app": {
            "name": "MyApp",
            "version": "1.0.0"
        },
        "database": {
            "url": "postgresql://localhost/myapp"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        json_file = f.name
    
    try:
        # Load from JSON
        config = ConfigurationProvider()
        config.from_json(json_file)
        
        print(f"✓ App name: {config.app.name()}")
        print(f"✓ App version: {config.app.version()}")
        print(f"✓ Database URL: {config.database.url()}")
    finally:
        os.unlink(json_file)


def test_environment_configuration():
    print("\n=== Testing Environment Configuration ===")
    
    # Set environment variables
    os.environ['APP_DEBUG'] = 'true'
    os.environ['APP_PORT'] = '8080'
    os.environ['APP_NAME'] = 'TestApp'
    
    try:
        config = ConfigurationProvider()
        
        # Load from environment
        debug = config.from_env('APP_DEBUG', as_=lambda x: x.lower() == 'true')
        port = config.from_env('APP_PORT', as_=int)
        name = config.from_env('APP_NAME')
        
        print(f"✓ Debug from env: {debug}")
        print(f"✓ Port from env: {port}")
        print(f"✓ Name from env: {name}")
        
    finally:
        # Clean up
        for key in ['APP_DEBUG', 'APP_PORT', 'APP_NAME']:
            os.environ.pop(key, None)


def test_configuration_with_providers():
    print("\n=== Testing Configuration with Providers ===")
    
    class AppContainer(BaseContainer):
        # Configuration
        config = ConfigurationProvider()
        
        # Providers using configuration
        database = SingletonProvider(
            DummyDatabase,
            connection_string=config.database.url
        )
        
        repository = SingletonProvider(
            DummyRepository,
            db=database
        )
        
        service = FactoryProvider(
            DummyService,
            repository=repository
        )
    
    # Create container and load config
    container = AppContainer()
    container.config.from_dict({
        "database": {
            "url": "config://database"
        }
    })
    
    # Use the service
    service = container.service()
    result = service.get_upper_case("configuration test")
    print(f"✓ Service with config: {result}")


def test_configuration_overrides():
    print("\n=== Testing Configuration Overrides ===")
    
    class AppContainer(BaseContainer):
        config = ConfigurationProvider()
        database = SingletonProvider(
            DummyDatabase,
            connection_string=config.database.url
        )
    
    # Production container
    prod_container = AppContainer()
    prod_container.config.from_dict({
        "database": {"url": "prod://database"}
    })
    
    # Test container with config override
    test_config = Configuration()
    test_config.from_dict({
        "database": {"url": "test://database"}
    })
    
    with prod_container.override_providers(config=test_config):
        test_db = prod_container.database()
        print(f"✓ Test database: {test_db.connection_string}")
    
    # Back to production
    prod_db = prod_container.database()
    print(f"✓ Production database: {prod_db.connection_string}")


def test_configuration_error_handling():
    print("\n=== Testing Configuration Error Handling ===")
    
    config = Configuration()
    
    # Test missing file
    try:
        config.from_json("nonexistent.json")
        print("✗ Should have raised error")
    except Exception as e:
        print(f"✓ Missing file error: {type(e).__name__}")
    
    # Test invalid type conversion
    try:
        config.from_dict({"port": "not_a_number"})
        config.port.as_int()()
        print("✗ Should have raised error")
    except Exception as e:
        print(f"✓ Type conversion error: {type(e).__name__}")
    
    # Test missing environment variable
    try:
        config.from_env("NONEXISTENT_VAR")
        print("✗ Should have raised error")
    except Exception as e:
        print(f"✓ Missing env var error: {type(e).__name__}")


if __name__ == "__main__":
    print("Testing Configuration Provider\n")
    
    test_basic_configuration()
    test_typed_configuration()
    test_json_configuration()
    test_environment_configuration()
    test_configuration_with_providers()
    test_configuration_overrides()
    test_configuration_error_handling()
    
    print("\n🎉 Configuration tests completed!")