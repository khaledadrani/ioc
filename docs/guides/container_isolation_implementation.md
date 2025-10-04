# Container Isolation Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the provider factory system to fix container shared state issues.

## Problem Summary

Currently, declarative containers share provider instances, causing configuration state to leak between container instances. The solution is to implement a provider factory system that creates fresh provider instances for each container.

## Implementation Steps

### Step 1: Create Provider Factory Infrastructure

#### 1.1 Add ProviderFactory Class

**File:** `ioc/providers/factory_system.py`

```python
from typing import Any, Dict, Optional
from .base import Provider

class ProviderFactory:
    """Factory for creating provider instances with dependency resolution."""
    
    def __init__(self, provider_class: type, *args: Any, **kwargs: Any):
        self.provider_class = provider_class
        self.args = args
        self.kwargs = kwargs
    
    def create(self, container_context: Optional['Container'] = None) -> Provider:
        """Create a fresh provider instance with resolved dependencies."""
        resolved_kwargs = {}
        
        for key, value in self.kwargs.items():
            if isinstance(value, ProviderFactory):
                # Recursive factory creation
                resolved_kwargs[key] = value.create(container_context)
            elif isinstance(value, ProviderRef):
                # Reference to another provider in container
                if container_context:
                    resolved_kwargs[key] = container_context.get_provider(value.name)
                else:
                    raise ValueError(f"Cannot resolve provider reference '{value.name}' without container context")
            else:
                # Direct value
                resolved_kwargs[key] = value
        
        return self.provider_class(*self.args, **resolved_kwargs)

class ProviderRef:
    """Reference to another provider in the container."""
    
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"ProviderRef('{self.name}')"
```

#### 1.2 Update Provider Base Class

**File:** `ioc/providers/base.py`

```python
# Add to Provider class:

def to_factory(self) -> 'ProviderFactory':
    """Convert this provider instance to a factory for cloning."""
    # Default implementation - subclasses should override
    return ProviderFactory(self.__class__)

def _get_factory_args(self) -> tuple:
    """Get arguments for factory creation. Override in subclasses."""
    return ()

def _get_factory_kwargs(self) -> dict:
    """Get keyword arguments for factory creation. Override in subclasses."""
    return {}
```

### Step 2: Update Provider Classes

#### 2.1 ConfigurationProvider

**File:** `ioc/providers/configuration.py`

```python
# Add to ConfigurationProvider class:

def to_factory(self):
    """Convert to factory for container isolation."""
    return ProviderFactory(
        ConfigurationProvider,
        self._name,
        default=None  # Don't copy data - each container should start fresh
    )

def _get_factory_args(self):
    return (self._name,)

def _get_factory_kwargs(self):
    return {'default': None}
```

#### 2.2 CallableProvider

**File:** `ioc/providers/callable.py`

```python
# Add to CallableProvider class:

def to_factory(self):
    """Convert to factory for container isolation."""
    factory_kwargs = {}
    
    for key, value in self.arguments.items():
        if isinstance(value, Provider):
            # Convert provider dependencies to references
            factory_kwargs[key] = value.to_factory()
        else:
            factory_kwargs[key] = value
    
    return ProviderFactory(
        CallableProvider,
        self.callable_obj,
        **factory_kwargs
    )

def _get_factory_args(self):
    return (self.callable_obj,)

def _get_factory_kwargs(self):
    return self.arguments.copy()
```

#### 2.3 FactoryProvider and SingletonProvider

**File:** `ioc/providers/factory.py` and `ioc/providers/singleton.py`

```python
# Add to both classes:

def to_factory(self):
    """Convert to factory for container isolation."""
    factory_kwargs = {}
    
    for key, value in self.arguments.items():
        if isinstance(value, Provider):
            factory_kwargs[key] = value.to_factory()
        else:
            factory_kwargs[key] = value
    
    return ProviderFactory(
        self.__class__,
        self.object_class,
        **factory_kwargs
    )

def _get_factory_args(self):
    return (self.object_class,)

def _get_factory_kwargs(self):
    return self.arguments.copy()
```

### Step 3: Update Container System

#### 3.1 Modify DeclarativeContainer Metaclass

**File:** `ioc/container.py`

```python
class DeclarativeContainer(type):
    """Metaclass for declarative container syntax with provider isolation."""
    
    def __new__(mcs, name, bases, attrs):
        # Store provider factories instead of instances
        provider_factories = {}
        
        # Inherit factories from base classes
        for base in bases:
            if hasattr(base, '_provider_factories'):
                provider_factories.update(base._provider_factories)
        
        # Convert provider instances to factories
        for key, value in list(attrs.items()):
            if isinstance(value, Provider):
                provider_factories[key] = value.to_factory()
        
        # Store factories in class
        attrs['_provider_factories'] = provider_factories
        
        # Create the class
        cls = super().__new__(mcs, name, bases, attrs)
        return cls
    
    def __call__(cls, **overrides):
        """Create container instance with isolated providers."""
        container = Container()
        
        # Create fresh provider instances from factories
        for name, factory in cls._provider_factories.items():
            provider = factory.create(container)
            container.set_provider(name, provider)
        
        # Apply overrides
        if overrides:
            container.override_providers(**overrides)
        
        return container
```

#### 3.2 Add Container Context Support

**File:** `ioc/container.py`

```python
# Add to Container class:

def get_provider(self, name: str) -> Provider:
    """Get provider by name for factory resolution."""
    if name in self.providers:
        return self.providers[name]
    raise KeyError(f"Provider '{name}' not found in container")
```

### Step 4: Handle Provider References

#### 4.1 Create Reference Resolution System

**File:** `ioc/providers/factory_system.py`

```python
def resolve_provider_references(provider_instance, container_context):
    """Recursively resolve provider references in a provider's arguments."""
    if hasattr(provider_instance, 'arguments'):
        for key, value in provider_instance.arguments.items():
            if isinstance(value, ProviderRef):
                # Replace reference with actual provider
                provider_instance.arguments[key] = container_context.get_provider(value.name)
            elif isinstance(value, Provider):
                # Recursively resolve nested providers
                resolve_provider_references(value, container_context)
```

#### 4.2 Update Factory Creation

```python
# In ProviderFactory.create():

def create(self, container_context: Optional['Container'] = None) -> Provider:
    """Create provider instance with full dependency resolution."""
    # ... existing code ...
    
    provider_instance = self.provider_class(*self.args, **resolved_kwargs)
    
    # Resolve any remaining provider references
    if container_context:
        resolve_provider_references(provider_instance, container_context)
    
    return provider_instance
```

### Step 5: Testing Strategy

#### 5.1 Container Isolation Tests

**File:** `tests/unit/test_container_isolation.py`

```python
def test_configuration_isolation():
    """Test that configuration changes don't leak between containers."""
    
    class TestContainer(BaseContainer):
        config = ConfigurationProvider("test")
        calculator = CallableProvider(calculate_tax, rate=config.tax.rate.as_float())
    
    # Create two containers
    container1 = TestContainer()
    container2 = TestContainer()
    
    # Load config in container1
    container1.config.from_dict({"tax": {"rate": "0.08"}})
    
    # container2 should not see container1's config
    with pytest.raises(ConfigurationNotLoadedError):
        container2.calculator(100.0)
    
    # Load different config in container2
    container2.config.from_dict({"tax": {"rate": "0.10"}})
    
    # Both containers should have independent configs
    assert container1.calculator(100.0) == 8.0
    assert container2.calculator(100.0) == 10.0

def test_singleton_isolation():
    """Test that singleton instances are isolated per container."""
    
    class Service:
        def __init__(self):
            self.value = random.randint(1, 1000)
    
    class TestContainer(BaseContainer):
        service = SingletonProvider(Service)
    
    container1 = TestContainer()
    container2 = TestContainer()
    
    # Each container should have its own singleton instance
    service1a = container1.service()
    service1b = container1.service()
    service2a = container2.service()
    
    assert service1a is service1b  # Same instance within container
    assert service1a is not service2a  # Different instances between containers
```

#### 5.2 Performance Tests

**File:** `tests/performance/test_container_performance.py`

```python
def test_container_creation_performance():
    """Ensure container creation performance is acceptable."""
    
    class LargeContainer(BaseContainer):
        # Create many providers to test performance
        config = ConfigurationProvider("test")
        services = [SingletonProvider(Service, id=i) for i in range(100)]
    
    start_time = time.time()
    containers = [LargeContainer() for _ in range(10)]
    end_time = time.time()
    
    creation_time = (end_time - start_time) / 10
    assert creation_time < 0.1  # Should create container in < 100ms
```

### Step 6: Migration and Compatibility

#### 6.1 Backward Compatibility

The implementation maintains full backward compatibility:

```python
# Existing code continues to work unchanged
class AppContainer(BaseContainer):
    config = ConfigurationProvider("app_config")
    tax_calculator = CallableProvider(calculate_tax, rate=config.tax.rate.as_float())

# Usage remains the same
container = AppContainer()
container.config.from_dict({"tax": {"rate": "0.08"}})
result = container.tax_calculator(100.0)
```

#### 6.2 Migration Checklist

- ✅ No changes required to existing container definitions
- ✅ No changes required to provider usage
- ✅ All existing tests should pass
- ✅ Performance impact should be minimal
- ✅ Memory usage increase should be reasonable

### Step 7: Documentation Updates

#### 7.1 Update Container Documentation

- Add explanation of container isolation
- Document the factory system (internal implementation)
- Add examples showing proper container usage
- Update troubleshooting guide

#### 7.2 Add Best Practices

```python
# ✅ Good: Each container is independent
container1 = AppContainer()
container2 = AppContainer()

# ✅ Good: Configuration is isolated
container1.config.from_dict(prod_config)
container2.config.from_dict(test_config)

# ✅ Good: Providers are independent
assert container1.service() is not container2.service()
```

## Implementation Timeline

### Week 1: Infrastructure
- Implement `ProviderFactory` and `ProviderRef` classes
- Add factory support to base `Provider` class
- Create comprehensive test framework

### Week 2: Provider Integration
- Update `ConfigurationProvider` with factory support
- Update `CallableProvider` with factory support
- Update `FactoryProvider` and `SingletonProvider`

### Week 3: Container System
- Modify `DeclarativeContainer` metaclass
- Implement provider reference resolution
- Add container context support

### Week 4: Testing and Validation
- Run full test suite
- Performance testing and optimization
- Documentation updates

## Success Metrics

- ✅ All existing tests pass
- ✅ Container isolation tests pass
- ✅ Performance degradation < 50%
- ✅ Memory usage increase < 100%
- ✅ Zero breaking changes to user API

This implementation will provide true container isolation while maintaining all existing functionality and backward compatibility.