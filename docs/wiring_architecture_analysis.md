# Wiring Architecture Analysis: Current vs Python DI Approach

## Current Implementation (Global Container Pattern)

### Architecture Overview

Our current wiring system uses a **global container context** approach for dependency injection:

```python
# Global state
_current_container = None

def wire(container, modules):
    _set_current_container(container)  # Set global reference

@inject
def my_function(service: Service = Provide('service')):
    pass  # Dependencies resolved at runtime using global container
```

### Key Components

#### 1. **Global Container Context**
```python
_current_container = None

def _get_current_container():
    return _current_container

def _set_current_container(container):
    global _current_container
    _current_container = container
```

#### 2. **Runtime Dependency Resolution**
```python
@inject
def wrapper(*args, **kwargs):
    container = _get_current_container()  # Get from global state
    injected_kwargs = _inject_dependencies(fn, container, kwargs)
    return fn(*args, **injected_kwargs)
```

#### 3. **Simple Wire Process**
```python
def wire(self, modules=None):
    _set_current_container(self)  # Just set global reference
    # Mark functions as wired for discovery
```

### Advantages
- ✅ **Simple implementation** (~120 lines of code)
- ✅ **Easy to understand** and maintain
- ✅ **Minimal memory overhead**
- ✅ **Works for single-container applications**
- ✅ **Fast development time**

### Disadvantages
- ❌ **Thread safety issues** - Global state shared across threads
- ❌ **Runtime overhead** - Dependencies resolved on every call
- ❌ **Single container limitation** - Can't have multiple active containers
- ❌ **Testing complexity** - Tests can interfere with each other
- ❌ **Hidden dependencies** - Functions depend on global state

## Python Dependency Injector Approach (Registry Pattern)

### Architecture Overview

Python DI uses a **pre-resolved dependency registry** approach:

```python
# Global registry of patched functions
_patched_registry = PatchedRegistry()

def wire(container, modules):
    # Pre-resolve ALL dependencies and store in registry
    for fn in find_injectable_functions(modules):
        resolved_deps = resolve_dependencies(fn, container)
        patched_fn = create_patched_function(fn, resolved_deps)
        _patched_registry.register(patched_fn)
```

### Key Components

#### 1. **Patched Function Registry**
```python
class PatchedRegistry:
    def __init__(self):
        self._callables = {}  # Maps original -> patched functions
    
    def register_callable(self, patched):
        self._callables[patched.original] = patched
```

#### 2. **Pre-Resolved Dependencies**
```python
class PatchedCallable:
    def __init__(self, original, injections):
        self.original = original
        self.injections = {}  # Pre-resolved provider instances
        
    def add_injection(self, param_name, provider):
        self.injections[param_name] = provider
```

#### 3. **Wire-Time Resolution**
```python
def wire(container, modules):
    providers_map = ProvidersMap(container)
    
    for module in modules:
        for fn in find_injectable_functions(module):
            # Resolve dependencies NOW, not at runtime
            resolved_deps = {}
            for param, marker in get_injection_markers(fn):
                provider = providers_map.resolve(marker.provider)
                resolved_deps[param] = provider
            
            # Create patched function with pre-resolved deps
            patched = PatchedCallable(fn, resolved_deps)
            _patched_registry.register(patched)
```

#### 4. **Runtime Execution**
```python
@inject
def wrapper(*args, **kwargs):
    patched = _patched_registry.get_callable(fn)
    
    # Use pre-resolved dependencies
    for param, provider in patched.injections.items():
        if param not in kwargs:
            kwargs[param] = provider()  # Just call, no resolution needed
    
    return fn(*args, **kwargs)
```

### Advantages
- ✅ **Thread safe** - No shared global container state
- ✅ **Better performance** - Dependencies pre-resolved
- ✅ **Multiple containers** - Each function stores its own deps
- ✅ **Early error detection** - Dependency issues found at wire-time
- ✅ **Better testing** - Functions can be independently patched

### Disadvantages
- ❌ **Complex implementation** (~300+ lines of code)
- ❌ **Higher memory usage** - Stores resolved dependencies
- ❌ **Longer development time**
- ❌ **More complex debugging**

## Comparison Matrix

| Aspect | Current (Global) | Python DI (Registry) | Winner |
|--------|------------------|----------------------|---------|
| **Implementation Complexity** | Simple (~120 LOC) | Complex (~300+ LOC) | Current |
| **Thread Safety** | Poor | Good | Python DI |
| **Runtime Performance** | Slower (resolve each call) | Faster (pre-resolved) | Python DI |
| **Memory Usage** | Low | Medium | Current |
| **Multiple Containers** | No | Yes | Python DI |
| **Error Detection** | Runtime | Wire-time | Python DI |
| **Development Speed** | Fast | Slow | Current |
| **Maintenance** | Easy | Complex | Current |

## Migration Analysis

### Required Changes for Registry Pattern

#### 1. **New Classes (Major Addition)**
```python
class PatchedRegistry:
    # ~50 lines - Function registry management
    
class PatchedCallable:
    # ~30 lines - Individual function patch data
    
class ProvidersMap:
    # ~80 lines - Container-to-provider mapping
```

#### 2. **Redesigned Core Functions**
```python
# inject() decorator - Complete rewrite (~40 lines)
# wire() method - Complete rewrite (~60 lines)  
# _resolve_provider() - Enhanced logic (~30 lines)
```

#### 3. **Impact Assessment**
- **Development Time**: 2-3 weeks
- **Code Changes**: ~70% of wiring.py rewritten
- **Testing**: Extensive regression testing needed
- **Breaking Changes**: Possible API changes

### Recommendation

**For Current State (70% Feature Parity):**

**Keep the Global Container Approach**

**Rationale:**
1. **Focus on Features**: Better to achieve 85% parity with missing providers
2. **Simplicity**: Current approach works and is maintainable
3. **Time Investment**: Registry pattern is optimization, not core functionality
4. **Risk vs Reward**: High implementation risk for moderate threading benefits

**Future Consideration:**
- Implement registry pattern in **v2.0** when feature-complete
- Consider it a performance optimization, not a core requirement
- Most DI usage is single-threaded web applications anyway

## Threading Workarounds

If threading becomes an issue with current approach:

### Option 1: Thread-Local Storage
```python
import threading

_context = threading.local()

def _get_current_container():
    return getattr(_context, 'container', None)

def _set_current_container(container):
    _context.container = container
```

### Option 2: Context Variables (Python 3.7+)
```python
import contextvars

_current_container = contextvars.ContextVar('container', default=None)

def _get_current_container():
    return _current_container.get()

def _set_current_container(container):
    _current_container.set(container)
```

Both options provide thread safety with **minimal code changes** (~5 lines) while keeping the simple architecture.

## Conclusion

The global container approach is a **pragmatic choice** for the current development phase. It provides:

- ✅ Working dependency injection
- ✅ Simple, maintainable code
- ✅ Fast development iteration
- ✅ Easy debugging and testing

The registry pattern is an **optimization** that can be considered later when:
- Feature parity is achieved (85%+)
- Performance becomes a bottleneck
- Multi-threading support is required
- Production-grade robustness is needed

**Current Priority**: Focus on missing provider types (Callable, Resource, List, Selector) to reach 85% parity rather than architectural optimization.