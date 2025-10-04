"""Container module for dependency injection."""

from .providers import Provider
from .wiring import WiringMixin


class Container(WiringMixin):
    """Dynamic container for managing providers."""
    
    def __init__(self):
        self.providers = {}
        self._overridden = []
    
    def __setattr__(self, name, value):
        """Automatically register providers when assigned as attributes."""
        if isinstance(value, Provider) and not name.startswith('_') and name != 'providers':
            if not hasattr(self, 'providers'):
                super().__setattr__('providers', {})
            self.providers[name] = value
        super().__setattr__(name, value)
    
    def __getattr__(self, name):
        """Get provider by name."""
        if name in self.providers:
            return self.providers[name]
        raise AttributeError(f"Container has no provider '{name}'")
    
    def set_provider(self, name, provider):
        """Explicitly set a provider."""
        if not isinstance(provider, Provider):
            raise TypeError("Only Provider instances can be registered")
        self.providers[name] = provider
        setattr(self, name, provider)
    
    def override_providers(self, **overrides):
        """Override multiple providers at once."""
        overridden = []
        for name, override_provider in overrides.items():
            if name in self.providers:
                self.providers[name].override(override_provider)
                overridden.append(self.providers[name])
        return ContainerOverrideContext(self, overridden)
    
    def reset_overrides(self):
        """Reset all provider overrides."""
        for provider in self.providers.values():
            provider.reset_override()
    



class DeclarativeContainer(type):
    """Metaclass for declarative container syntax."""
    
    def __new__(mcs, name, bases, attrs):
        # Extract providers from class attributes
        providers = {}
        
        # Inherit providers from base classes
        for base in bases:
            if hasattr(base, '_class_providers'):
                providers.update(base._class_providers)
        
        # Add current class providers
        for key, value in list(attrs.items()):
            if isinstance(value, Provider):
                providers[key] = value
        
        # Store providers in class
        attrs['_class_providers'] = providers
        
        # Create the class
        cls = super().__new__(mcs, name, bases, attrs)
        return cls
    
    def __call__(cls, **overrides):
        """Create container instance with optional provider overrides."""
        container = Container()
        
        # Copy providers from class
        for name, provider in cls._class_providers.items():
            # Create a copy of the provider to avoid shared state
            container.set_provider(name, provider)
        
        # Apply overrides
        if overrides:
            container.override_providers(**overrides)
        
        return container


class ContainerOverrideContext:
    """Context manager for container provider overrides."""
    
    def __init__(self, container, overridden_providers):
        self.container = container
        self.overridden_providers = overridden_providers
    
    def __enter__(self):
        return self.container
    
    def __exit__(self, *args):
        for provider in self.overridden_providers:
            provider.reset_override()


# Base class for declarative containers
class BaseContainer(metaclass=DeclarativeContainer):
    """Base class for declarative dependency injection containers."""
    pass