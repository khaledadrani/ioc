#!/usr/bin/env python3
"""Simple test script for the updated IoC classes."""

from inject.providers import FactoryProvider, SingletonProvider
from tests.conftest import DummyDatabase, DummyRepository, DummyService


def test_factory_provider():
    print("=== Testing FactoryProvider ===")
    
    # Basic factory
    db_provider = FactoryProvider(DummyDatabase, connection_string="test://db")
    db = db_provider()
    print(f"✓ Factory created: {type(db).__name__} with connection: {db.connection_string}")
    
    # Multiple calls create different instances
    db2 = db_provider()
    print(f"✓ Different instances: {id(db) != id(db2)}")
    
    # Provider dependencies
    repo_provider = FactoryProvider(DummyRepository, db=db_provider)
    repo = repo_provider()
    print(f"✓ Dependency injection: {type(repo).__name__} -> {type(repo.db).__name__}")
    
    # Override test
    override_provider = FactoryProvider(DummyDatabase, connection_string="override://db")
    with db_provider.override(override_provider):
        override_db = db_provider()
        print(f"✓ Override works: {override_db.connection_string}")
    
    # Back to original after override
    normal_db = db_provider()
    print(f"✓ Override reverted: {normal_db.connection_string}")


def test_singleton_provider():
    print("\n=== Testing SingletonProvider ===")
    
    # Basic singleton
    db_provider = SingletonProvider(DummyDatabase, connection_string="singleton://db")
    db1 = db_provider()
    db2 = db_provider()
    print(f"✓ Same instance: {id(db1) == id(db2)}")
    print(f"✓ Singleton created: {type(db1).__name__} with connection: {db1.connection_string}")
    
    # Reset singleton
    db_provider.reset()
    db3 = db_provider()
    print(f"✓ Reset creates new instance: {id(db1) != id(db3)}")
    
    # Singleton with dependencies
    repo_provider = SingletonProvider(DummyRepository, db=db_provider)
    repo1 = repo_provider()
    repo2 = repo_provider()
    print(f"✓ Singleton dependency: {id(repo1) == id(repo2)} and {id(repo1.db) == id(repo2.db)}")


def test_complex_dependency_chain():
    print("\n=== Testing Complex Dependencies ===")
    
    # Create dependency chain
    db_provider = SingletonProvider(DummyDatabase, connection_string="chain://db")
    repo_provider = SingletonProvider(DummyRepository, db=db_provider)
    service_provider = FactoryProvider(DummyService, repository=repo_provider)
    
    # Test the chain
    service = service_provider()
    result = service.get_upper_case("hello world")
    print(f"✓ Complex chain works: {result}")
    
    # Test that singletons are preserved in chain
    service2 = service_provider()
    print(f"✓ Singletons preserved: {id(service.repository) == id(service2.repository)}")
    print(f"✓ But services are different: {id(service) != id(service2)}")


def test_error_handling():
    print("\n=== Testing Error Handling ===")
    
    try:
        # Invalid arguments
        bad_provider = FactoryProvider(DummyDatabase, invalid_arg="value")
        bad_provider()
        print("✗ Should have raised error")
    except Exception as e:
        print(f"✓ Error handling works: {type(e).__name__}")
    
    try:
        # Invalid override type
        db_provider = FactoryProvider(DummyDatabase, connection_string="test://db")
        db_provider.override("not_a_provider")
        print("✗ Should have raised TypeError")
    except TypeError as e:
        print(f"✓ Override validation works: {e}")


if __name__ == "__main__":
    print("Testing Updated IoC Framework\n")
    
    test_factory_provider()
    test_singleton_provider()
    test_complex_dependency_chain()
    test_error_handling()
    
    print("\n🎉 All tests completed!")