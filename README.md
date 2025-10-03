# Inject - Python Dependency Injection Framework

A modern, lightweight dependency injection framework for Python projects with automatic wiring and configuration management.

## Current Status: 70% Feature Parity with Python Dependency Injector

### ✅ Implemented Features

- **Provider System**: Factory and Singleton providers with overriding support
- **Container Architecture**: Dynamic and declarative containers with metaclass support
- **Configuration Management**: JSON/YAML loading with environment variable support
- **Automatic Wiring**: `@inject` decorator with `Provide` markers
- **Resource Lifecycle**: Context manager support for proper cleanup
- **Comprehensive Testing**: 76+ unit tests with real-world examples

## Quick Start

```python
from inject import Container, FactoryProvider, inject, Provide

# Define your services
class Database:
    def __init__(self, url: str):
        self.url = url

class UserService:
    def __init__(self, db: Database):
        self.db = db

# Configure container
class AppContainer(Container):
    database = FactoryProvider(Database, url="sqlite:///app.db")
    user_service = FactoryProvider(UserService, db=database)

# Use automatic wiring
@inject
def get_user(user_id: int, service: UserService = Provide('user_service')):
    return service.get_user(user_id)

# Wire the container
container = AppContainer()
container.wire(modules=[__name__])
```

## Configuration Support

```python
from inject import ConfigurationProvider

# Load from YAML/JSON
config = ConfigurationProvider()
config.from_yaml('config.yaml')

class AppContainer(Container):
    database = FactoryProvider(
        Database, 
        url=config.database.url,
        port=config.database.port.as_int()
    )
```

## Provider Overriding

```python
# Override for testing
test_db = FactoryProvider(TestDatabase, url="sqlite:///:memory:")

with container.database.override(test_db):
    # Uses test database
    result = get_user(123)
```

## Installation & Build

```bash
# Build the library
python setup.py bdist_wheel

# Install for development
pip install -e .

# Run tests
python -m pytest tests/
```

## Architecture

- **Base Provider**: Foundation class with overriding and context management
- **Factory Provider**: Creates new instances on each call
- **Singleton Provider**: Caches instances with thread-safe access
- **Configuration Provider**: Manages app configuration with type conversion
- **Container System**: Declarative and dynamic container support
- **Wiring System**: Automatic dependency injection with decorators

## Roadmap

### Next Phase (Target: 85% Parity)
- **Additional Providers**: Callable, Resource, List, Selector providers
- **Enhanced Injection**: Positional and attribute injection methods
- **Async Support**: Coroutine providers and async resource management

### Future Enhancements
- **Performance**: Cython optimization for production use
- **Type System**: Full type hint support with mypy compatibility
- **Advanced Features**: Circular dependency detection, provider traversal

## Comparison with Python Dependency Injector

| Feature | Python DI | Inject | Status |
|---------|-----------|--------|---------|
| Core Providers | ✅ | ✅ | Complete |
| Container System | ✅ | ✅ | Complete |
| Configuration | ✅ | ✅ | Complete |
| Wiring | ✅ | ✅ | Complete |
| Provider Types | 15+ | 2 | In Progress |
| Async Support | ✅ | ❌ | Planned |
| Performance | Cython | Python | Future |

## Contributing

The framework has a solid foundation with comprehensive test coverage. See `docs/` for detailed implementation analysis and development guides.

## License

MIT License - see LICENSE file for details.