# Convention-Based Dependency Injection

## Overview

The IoC framework supports two injection styles:

1. **Explicit Injection** - Using `@inject` with `Provide()` markers (default)
2. **Convention-Based Injection** - Using `@auto_inject` with parameter name matching (Spring Boot style)

## Convention-Based Injection

### Basic Usage

```python
from ioc import Container, FactoryProvider, auto_inject

class UserRepository:
    def get_user(self, user_id: int):
        return f"User {user_id}"

class AppContainer(Container):
    user_repository = FactoryProvider(UserRepository)

# Convention-based injection - parameter name matches provider name
@auto_inject
def get_user_info(user_id: int, user_repository: UserRepository):
    return user_repository.get_user(user_id)

# Wire container
container = AppContainer()
container.wire(modules=[__name__])

# Call function - user_repository automatically injected
result = get_user_info(123)  # Returns "User 123"
```

### How It Works

1. **Parameter Name Matching** - Function parameter names must match container provider names exactly
2. **Type Checking** - Optional runtime type validation using type hints
3. **Automatic Resolution** - No `Provide()` markers needed

### Comparison with Explicit Injection

| Feature | Explicit (`@inject`) | Convention (`@auto_inject`) |
|---------|---------------------|----------------------------|
| **Syntax** | `repo: UserRepository = Provide('user_repository')` | `user_repository: UserRepository` |
| **Parameter Names** | Flexible | Must match provider names |
| **Clarity** | Explicit dependencies | Implicit dependencies |
| **Boilerplate** | More verbose | Cleaner |
| **Refactoring** | Safe | Parameter renames break injection |

## Advanced Usage

### Type Validation

```python
@auto_inject
def process_user(user_id: int, user_repository: UserRepository, email_service: EmailService):
    # Runtime type checking ensures correct types are injected
    user = user_repository.get_user(user_id)
    return email_service.send_welcome(user)
```

### Mixed Parameters

```python
@auto_inject
def create_user(name: str, email: str, user_repository: UserRepository):
    # Regular parameters (name, email) + injected parameter (user_repository)
    return user_repository.create(name=name, email=email)
```

### Error Handling

```python
# This will raise ConventionInjectionError
@auto_inject
def bad_function(user_id: int, missing_service: SomeService):
    # Error: No provider named 'missing_service' in container
    pass

# This will raise ConventionInjectionError  
@auto_inject
def type_mismatch(user_id: int, user_repository: WrongType):
    # Error: Provider returns UserRepository, but parameter expects WrongType
    pass
```

## Container Setup

### Provider Naming Convention

```python
class AppContainer(Container):
    # Provider names must match parameter names exactly
    user_repository = FactoryProvider(UserRepository, db=database)
    email_service = SingletonProvider(EmailService, smtp_host="localhost")
    cache_service = SingletonProvider(CacheService, host="redis")
```

### Nested Provider Access

```python
class AppContainer(Container):
    database = SingletonProvider(Database, host="localhost")
    
    # For nested access, use the full path as parameter name
    # This is less common with convention-based injection
```

## Best Practices

### 1. Consistent Naming

```python
# Good - consistent naming
class AppContainer(Container):
    user_repository = FactoryProvider(UserRepository)
    email_service = FactoryProvider(EmailService)

@auto_inject
def process_user(user_id: int, user_repository: UserRepository, email_service: EmailService):
    pass
```

### 2. Use Type Hints

```python
# Good - enables type checking
@auto_inject
def get_user(user_id: int, user_repository: UserRepository) -> User:
    return user_repository.get_user(user_id)

# Avoid - no type checking
@auto_inject
def get_user(user_id: int, user_repository):
    return user_repository.get_user(user_id)
```

### 3. Keep Parameter Names Stable

```python
# Avoid renaming parameters as it breaks injection
@auto_inject
def get_user(user_id: int, user_repo: UserRepository):  # ❌ Won't work
    return user_repo.get_user(user_id)

@auto_inject  
def get_user(user_id: int, user_repository: UserRepository):  # ✅ Works
    return user_repository.get_user(user_id)
```

## When to Use Convention-Based Injection

### Use Convention-Based When:
- ✅ You prefer Spring Boot style injection
- ✅ You want cleaner function signatures
- ✅ You have consistent naming conventions
- ✅ You're building new applications

### Use Explicit Injection When:
- ✅ You need flexible parameter naming
- ✅ You want explicit dependency documentation
- ✅ You're working with existing codebases
- ✅ You need complex provider paths

## Migration Guide

### From Explicit to Convention-Based

```python
# Before (explicit)
@inject
def get_user(user_id: int, repo: UserRepository = Provide('user_repository')):
    return repo.get_user(user_id)

# After (convention-based)
@auto_inject
def get_user(user_id: int, user_repository: UserRepository):
    return user_repository.get_user(user_id)
```

### Gradual Migration

```python
# You can use both styles in the same application
@inject
def legacy_function(repo: UserRepository = Provide('user_repository')):
    return repo.get_all()

@auto_inject
def new_function(user_repository: UserRepository):
    return user_repository.get_all()
```

## Error Reference

### ConventionInjectionError

Raised when convention-based injection fails:

```python
# Provider not found
ConventionInjectionError: No provider found for parameter 'missing_service'

# Type mismatch
ConventionInjectionError: Parameter 'user_repository' expects UserRepository, got DatabaseConnection

# Not callable
ConventionInjectionError: 'user_repository' is not a callable provider
```

## Complete Example

```python
from ioc import Container, FactoryProvider, SingletonProvider, auto_inject

# Domain classes
class Database:
    def __init__(self, host: str):
        self.host = host

class UserRepository:
    def __init__(self, database: Database):
        self.database = database
    
    def get_user(self, user_id: int):
        return f"User {user_id} from {self.database.host}"

class EmailService:
    def __init__(self, smtp_host: str):
        self.smtp_host = smtp_host
    
    def send_welcome(self, user: str):
        return f"Welcome email sent to {user} via {self.smtp_host}"

# Container with convention-friendly naming
class AppContainer(Container):
    database = SingletonProvider(Database, host="localhost")
    user_repository = FactoryProvider(UserRepository, database=database)
    email_service = SingletonProvider(EmailService, smtp_host="smtp.example.com")

# Convention-based functions
@auto_inject
def get_user_info(user_id: int, user_repository: UserRepository) -> str:
    return user_repository.get_user(user_id)

@auto_inject
def welcome_user(user_id: int, user_repository: UserRepository, email_service: EmailService) -> str:
    user = user_repository.get_user(user_id)
    return email_service.send_welcome(user)

# Usage
if __name__ == "__main__":
    container = AppContainer()
    container.wire(modules=[__name__])
    
    user_info = get_user_info(123)
    welcome_msg = welcome_user(456)
    
    print(user_info)    # User 123 from localhost
    print(welcome_msg)  # Welcome email sent to User 456 from localhost via smtp.example.com
```

This convention-based approach provides a cleaner, Spring Boot-like experience while maintaining the flexibility to use explicit injection when needed.