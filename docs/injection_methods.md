# Dependency Injection Methods

This document explains the four main methods of dependency injection supported by modern IoC frameworks like Python Dependency Injector.

## 1. Keyword Arguments Injection ✅

**What it is**: Dependencies are injected as keyword arguments to functions or constructors.

**How it works**: The injection framework identifies parameters with dependency markers and provides the resolved dependencies as keyword arguments.

### Example
```python
@inject
def process_user(user_id: int, db: Database = Provide('database')):
    return db.get_user(user_id)

# Framework calls: process_user(user_id=123, db=<Database instance>)
```

### Advantages
- Simple and explicit
- Works with existing function signatures
- Easy to understand and debug

### Disadvantages
- Requires default values in function signature
- Can clutter function definitions

## 2. Positional Arguments Injection ❌

**What it is**: Dependencies are injected as positional arguments based on parameter order and type hints.

**How it works**: The framework analyzes function signatures and injects dependencies in the correct positional order before user-provided arguments.

### Example
```python
@inject
def process_user(db: Database, cache: Cache, user_id: int):
    # db and cache are injected positionally
    # user_id is provided by caller
    return db.get_user(user_id)

# Call: process_user(user_id=123)
# Framework calls: process_user(<Database>, <Cache>, user_id=123)
```

### Advantages
- Cleaner function signatures (no default values needed)
- More natural parameter ordering
- Better IDE support with type hints

### Disadvantages
- More complex injection logic
- Parameter order matters
- Can be confusing without clear documentation

## 3. Attribute Injection ❌

**What it is**: Dependencies are injected directly into class attributes after object construction.

**How it works**: The framework scans class definitions for dependency markers and sets the corresponding attributes on instances after calling `__init__`.

### Example
```python
class UserService:
    database = Dependency()  # Marker for injection
    cache = Dependency()
    
    def __init__(self, config: str):
        self.config = config
        # database and cache will be injected here automatically
    
    def get_user(self, user_id: int):
        return self.database.get_user(user_id)

# Usage
service = container.user_service()
# service.database and service.cache are automatically set
```

### Advantages
- Clean separation of dependencies from constructor logic
- No need to modify `__init__` method
- Dependencies are clearly visible at class level

### Disadvantages
- Dependencies not available during `__init__`
- Can make testing more complex
- Less explicit than constructor injection

## 4. Method Injection ❌

**What it is**: Dependencies are injected into specific methods when they are called, rather than at object construction time.

**How it works**: Individual methods are decorated or marked for injection, and dependencies are resolved fresh for each method call.

### Example
```python
class UserService:
    def __init__(self, config: str):
        self.config = config
    
    @inject
    def get_user(self, user_id: int, 
                db: Database = Provide('database'),
                logger: Logger = Provide('logger')):
        logger.info(f"Getting user {user_id}")
        return db.get_user(user_id)
    
    @inject
    def update_user(self, user_id: int, data: dict,
                   db: Database = Provide('database')):
        return db.update_user(user_id, data)

# Dependencies resolved per method call
```

### Advantages
- Fine-grained control over dependency resolution
- Different methods can have different dependencies
- Dependencies resolved fresh for each call
- Good for stateless services

### Disadvantages
- Injection overhead on every method call
- Can lead to repeated dependency resolution
- More complex to implement and debug

## Comparison Matrix

| Method | Complexity | Performance | Flexibility | Current Support |
|--------|------------|-------------|-------------|-----------------|
| Kwargs Injection | Low | Good | Medium | ✅ Implemented |
| Positional Injection | Medium | Good | High | ❌ Missing |
| Attribute Injection | Medium | Best | Medium | ❌ Missing |
| Method Injection | High | Poor | High | ❌ Missing |

## When to Use Each Method

### Kwargs Injection
- **Best for**: Functions, simple services, getting started
- **Use when**: You want explicit, easy-to-understand injection

### Positional Injection
- **Best for**: Clean APIs, type-hint heavy codebases
- **Use when**: You want minimal function signature pollution

### Attribute Injection
- **Best for**: Complex classes with many dependencies
- **Use when**: Dependencies don't need to be available during `__init__`

### Method Injection
- **Best for**: Stateless services, per-request dependencies
- **Use when**: Different methods need different dependency sets

## Implementation Status in Your Framework

**Currently Implemented:**
- ✅ Kwargs Injection - Full support with `@inject` decorator

**Missing Implementations:**
- ❌ Positional Injection - Requires signature analysis and argument reordering
- ❌ Attribute Injection - Requires class scanning and post-construction injection
- ❌ Method Injection - Requires per-method dependency resolution

## Next Steps

To achieve full injection method support:

1. **Implement Positional Injection** - Analyze function signatures and inject dependencies in correct order
2. **Add Attribute Injection** - Scan class attributes and inject after construction
3. **Support Method Injection** - Enable per-method dependency resolution

This would bring your framework to feature parity with Python Dependency Injector's injection capabilities.