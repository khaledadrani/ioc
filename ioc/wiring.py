"""Automatic dependency injection wiring system."""

import contextvars
import functools
import inspect
from typing import Any, Callable, Dict, Optional, Type, Union


class Provide:
    """Marker for automatic dependency injection."""
    
    def __init__(self, provider: Any):
        self.provider = provider
    
    def __repr__(self):
        return f"Provide({self.provider})"


def inject(fn: Callable) -> Callable:
    """Decorator for automatic dependency injection."""
    
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # Get the container from the current context
        container = _get_current_container()
        if not container:
            return fn(*args, **kwargs)
        
        # Inject dependencies
        injected_kwargs = _inject_dependencies(fn, container, kwargs)
        return fn(*args, **injected_kwargs)
    
    wrapper.__wired__ = True
    return wrapper


def _inject_dependencies(fn: Callable, container: Any, provided_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Inject dependencies into function arguments."""
    sig = inspect.signature(fn)
    injected_kwargs = provided_kwargs.copy()
    
    for param_name, param in sig.parameters.items():
        # Skip if already provided
        if param_name in provided_kwargs:
            continue
        
        # Check if parameter has Provide annotation
        if isinstance(param.default, Provide):
            provider = param.default.provider
            try:
                # Resolve provider path in container
                value = _resolve_provider(container, provider)
                injected_kwargs[param_name] = value
            except Exception:
                # If injection fails and no default, let function handle it
                if param.default is inspect.Parameter.empty:
                    continue
    
    return injected_kwargs


def _resolve_provider(container: Any, provider: Any) -> Any:
    """Resolve provider from container."""
    if isinstance(provider, str):
        # String path like "database.connection"
        parts = provider.split('.')
        obj = container
        for part in parts:
            obj = getattr(obj, part)
        return obj()
    else:
        # Direct provider reference
        return provider()


# Context variable for container (thread-safe)
_current_container = contextvars.ContextVar('container', default=None)


def _get_current_container():
    """Get the current container from context."""
    return _current_container.get()


def _set_current_container(container):
    """Set the current container context."""
    _current_container.set(container)


class WiringMixin:
    """Mixin to add wiring capabilities to containers."""
    
    def wire(self, modules: Optional[list] = None, packages: Optional[list] = None):
        """Wire container to modules/packages for automatic injection."""
        _set_current_container(self)
        
        if modules:
            for module in modules:
                self._wire_module(module)
        
        if packages:
            for package in packages:
                self._wire_package(package)
    
    def unwire(self):
        """Remove wiring from container."""
        if _get_current_container() is self:
            _set_current_container(None)
    
    def _wire_module(self, module):
        """Wire all functions in a module."""
        import types
        
        if isinstance(module, str):
            module = __import__(module, fromlist=[''])
        
        for name in dir(module):
            obj = getattr(module, name)
            if (inspect.isfunction(obj) and 
                hasattr(obj, '__wired__') and 
                not getattr(obj, '__injected__', False)):
                # Mark as injected to avoid double-wiring
                obj.__injected__ = True
    
    def _wire_package(self, package):
        """Wire all modules in a package."""
        import pkgutil
        import importlib
        
        if isinstance(package, str):
            package = importlib.import_module(package)
        
        for _, name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            try:
                module = importlib.import_module(name)
                self._wire_module(module)
            except ImportError:
                continue