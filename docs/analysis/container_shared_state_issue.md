# Container Shared State Issue Analysis

## Problem Statement

**Issue:** Declarative containers share provider instances across all container instances, causing configuration state to leak between containers.

**Impact:** When multiple container instances are created from the same declarative container class, they share the same provider objects. This means configuration loaded in one container affects all other containers.

## Current Behavior (Broken)

```python
class AppContainer(BaseContainer):
    config = ConfigurationProvider("app_config")
    tax_calculator = CallableProvider(calculate_tax, rate=config.tax.rate.as_float())

# Problem: Both containers share the SAME provider instances
container1 = AppContainer()
container2 = AppContainer()

# Loading config in container1 affects container2
container1.config.from_dict({"tax": {"rate": "0.08"}})
result = container2.tax_calculator(100.0)  # Uses 0.08 rate from container1!
```

## Root Cause Analysis

### **DeclarativeContainer Metaclass Issue**

In `container.py`, the `DeclarativeContainer.__call__()` method:

```python
for name, provider in cls._class_providers.items():
    # BUG: Shares the same provider instance across containers
    container.set_provider(name, provider)
```

### **Why This Happens**

1. **Class-level providers** are created once when the container class is defined
2. **All container instances** reference the same provider objects
3. **Stateful providers** (like ConfigurationProvider) maintain shared state
4. **Configuration changes** in one container affect all containers

### **Affected Provider Types**

- ✅ **ConfigurationProvider** - Shares `_data` dict across containers
- ✅ **SingletonProvider** - Shares `_instance` across containers  
- ⚠️ **CallableProvider** - Shares dependencies that may be stateful
- ⚠️ **FactoryProvider** - Shares dependencies that may be stateful

## Proposed Solution: Provider Factory System

### **Architecture Overview**

Replace direct provider instances with **provider factories** that create fresh instances when containers are instantiated.

### **Core Components**

#### **1. ProviderFactory Class**
```python
class ProviderFactory:
    """Factory for creating provider instances."""
    def __init__(self, provider_class, *args, **kwargs):
        self.provider_class = provider_class
        self.args = args
        self.kwargs = kwargs
    
    def create(self, container_context=None):
        """Create a fresh provider instance."""
        resolved_kwargs = {}
        for k, v in self.kwargs.items():
            if isinstance(v, ProviderFactory):
                resolved_kwargs[k] = v.create(container_context)
            elif isinstance(v, ProviderRef):
                resolved_kwargs[k] = container_context.get_provider(v.name)
            else:
                resolved_kwargs[k] = v
        
        return self.provider_class(*self.args, **resolved_kwargs)
```

#### **2. ProviderRef Class**
```python
class ProviderRef:
    """Reference to another provider in the container."""
    def __init__(self, name):
        self.name = name
```

#### **3. Updated DeclarativeContainer**
```python
class DeclarativeContainer(type):
    def __new__(mcs, name, bases, attrs):
        provider_factories = {}
        
        for base in bases:
            if hasattr(base, '_provider_factories'):
                provider_factories.update(base._provider_factories)
        
        # Convert provider instances to factories
        for key, value in list(attrs.items()):
            if isinstance(value, Provider):
                provider_factories[key] = self._create_factory(value)
        
        attrs['_provider_factories'] = provider_factories
        return super().__new__(mcs, name, bases, attrs)
    
    def __call__(cls, **overrides):
        container = Container()
        
        # Create fresh provider instances from factories
        for name, factory in cls._provider_factories.items():
            provider = factory.create(container)
            container.set_provider(name, provider)
        
        return container
```

### **Implementation Benefits**

#### **✅ Advantages**
- **True Isolation** - Each container gets completely independent providers
- **Zero Breaking Changes** - Existing syntax works unchanged
- **Maintains Relationships** - Provider dependencies are preserved correctly
- **No Circular Imports** - Factories resolve dependencies at runtime
- **All Features Preserved** - Overriding, wiring, inheritance all work

#### **⚠️ Considerations**
- **Increased Complexity** - More moving parts in container system
- **Memory Overhead** - Each container has its own provider instances
- **Implementation Effort** - Requires changes to provider classes

### **Alternative Solutions Considered**

#### **1. Deep Copy Approach**
```python
# Pros: Simple implementation
# Cons: Fails with complex objects, circular references
import copy
cloned_provider = copy.deepcopy(provider)
```

#### **2. Provider Clone Methods**
```python
# Pros: Controlled copying per provider type
# Cons: Circular import issues, complex dependency resolution
def clone(self):
    return self.__class__(**self._original_kwargs)
```

#### **3. Lazy Initialization**
```python
# Pros: Defers provider creation
# Cons: Complex lifecycle management, unclear semantics
```

## Implementation Plan

### **Phase 1: Core Factory System**
1. Implement `ProviderFactory` and `ProviderRef` classes
2. Add factory creation logic to `DeclarativeContainer`
3. Update provider classes to support factory creation

### **Phase 2: Provider Integration**
1. Add factory support to `ConfigurationProvider`
2. Add factory support to `CallableProvider`
3. Add factory support to `FactoryProvider` and `SingletonProvider`

### **Phase 3: Testing & Validation**
1. Create comprehensive test suite for container isolation
2. Verify all existing functionality still works
3. Performance testing for memory and speed impact

### **Phase 4: Documentation & Examples**
1. Update container documentation
2. Add examples showing proper container isolation
3. Migration guide (if any breaking changes)

## Risk Assessment

### **Low Risk Areas**
- **API Compatibility** - No changes to user-facing API
- **Feature Preservation** - All current features maintained
- **Incremental Implementation** - Can be done step by step

### **Medium Risk Areas**
- **Performance Impact** - More objects created per container
- **Memory Usage** - Each container has independent providers
- **Complex Dependencies** - Need to handle circular references

### **Mitigation Strategies**
- **Comprehensive Testing** - Extensive test coverage for edge cases
- **Gradual Rollout** - Implement one provider type at a time
- **Fallback Mechanism** - Keep current behavior as backup option

## Success Criteria

### **Functional Requirements**
- ✅ Container instances are completely isolated
- ✅ Configuration changes don't leak between containers
- ✅ All existing features continue to work
- ✅ No breaking changes to user code

### **Performance Requirements**
- ✅ Container creation time < 2x current performance
- ✅ Memory usage increase < 50% per container
- ✅ Provider resolution time unchanged

### **Quality Requirements**
- ✅ 100% test coverage for new factory system
- ✅ All existing tests continue to pass
- ✅ Documentation updated and comprehensive

## Conclusion

The provider factory system is the recommended solution for fixing the container shared state issue. It provides true isolation while maintaining backward compatibility and all existing features.

**Next Steps:**
1. Create detailed implementation plan
2. Begin Phase 1 implementation
3. Set up comprehensive testing framework
4. Document progress in work sessions

**Priority:** High - This is a fundamental architectural issue that affects the reliability of the dependency injection system.