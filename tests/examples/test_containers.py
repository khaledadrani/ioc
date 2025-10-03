#!/usr/bin/env python3
"""Test script for the new Container system."""

from inject.providers import FactoryProvider, SingletonProvider
from inject.container import Container, BaseContainer
from tests.conftest import DummyDatabase, DummyRepository, DummyService


def test_dynamic_container():
    print("=== Testing Dynamic Container ===")
    
    # Create container and add providers
    container = Container()
    container.database = SingletonProvider(DummyDatabase, connection_string="container://db")
    container.repository = SingletonProvider(DummyRepository, db=container.database)
    container.service = FactoryProvider(DummyService, repository=container.repository)
    
    print(f"✓ Container has {len(container.providers)} providers")
    
    # Use the providers
    service = container.service()
    result = service.get_upper_case("hello container")
    print(f"✓ Service works: {result}")
    
    # Test provider access
    db1 = container.database()
    db2 = container.database()
    print(f"✓ Singleton through container: {id(db1) == id(db2)}")


def test_declarative_container():
    print("\n=== Testing Declarative Container ===")
    
    # Define container class
    class AppContainer(BaseContainer):
        database = SingletonProvider(DummyDatabase, connection_string="declarative://db")
        repository = SingletonProvider(DummyRepository, db=database)
        service = FactoryProvider(DummyService, repository=repository)
    
    # Create container instance
    container = AppContainer()
    
    print(f"✓ Declarative container created with {len(container.providers)} providers")
    
    # Use the services
    service = container.service()
    result = service.get_upper_case("declarative style")
    print(f"✓ Declarative service works: {result}")


def test_container_overrides():
    print("\n=== Testing Container Overrides ===")
    
    class AppContainer(BaseContainer):
        database = SingletonProvider(DummyDatabase, connection_string="prod://db")
        repository = SingletonProvider(DummyRepository, db=database)
        service = FactoryProvider(DummyService, repository=repository)
    
    # Create container
    container = AppContainer()
    
    # Test original
    original_service = container.service()
    original_result = original_service.get_upper_case("original")
    print(f"✓ Original: {original_result}")
    
    # Test with overrides
    test_db = SingletonProvider(DummyDatabase, connection_string="test://db")
    
    with container.override_providers(database=test_db):
        test_service = container.service()
        test_result = test_service.get_upper_case("overridden")
        print(f"✓ Overridden: {test_result}")
    
    # Test back to original
    after_service = container.service()
    after_result = after_service.get_upper_case("after override")
    print(f"✓ After override: {after_result}")


def test_container_with_runtime_overrides():
    print("\n=== Testing Runtime Container Creation ===")
    
    class AppContainer(BaseContainer):
        database = SingletonProvider(DummyDatabase, connection_string="default://db")
        repository = SingletonProvider(DummyRepository, db=database)
    
    # Create with overrides at instantiation
    test_db = SingletonProvider(DummyDatabase, connection_string="runtime://db")
    container = AppContainer(database=test_db)
    
    repo = container.repository()
    print(f"✓ Runtime override: {repo.db.connection_string}")


def test_error_handling():
    print("\n=== Testing Container Error Handling ===")
    
    container = Container()
    
    try:
        container.set_provider("test", "not_a_provider")
        print("✗ Should have raised TypeError")
    except TypeError as e:
        print(f"✓ Provider validation: {e}")
    
    try:
        _ = container.nonexistent
        print("✗ Should have raised AttributeError")
    except AttributeError as e:
        print(f"✓ Missing provider error: {e}")


if __name__ == "__main__":
    print("Testing Container System\n")
    
    test_dynamic_container()
    test_declarative_container()
    test_container_overrides()
    test_container_with_runtime_overrides()
    test_error_handling()
    
    print("\n🎉 Container tests completed!")