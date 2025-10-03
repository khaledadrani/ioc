from __future__ import annotations

from functools import partial
from typing import Any, Dict, Type, Optional
from .exceptions import ProvideObjectError
from .base_provider import Provider
from .config_provider import ConfigurationProvider, ConfigurationOption, TypedConfigurationOption


class FactoryProvider(Provider):
    def __init__(self, object_class: Type[Any], **kwargs: Any) -> None:
        super().__init__()
        self.object_class: Type[Any] = object_class
        self.arguments: Dict[str, Any] = kwargs
        self.dependencies: Dict[str, Provider] = {
            k: v for k, v in self.arguments.items() if isinstance(v, Provider)
        }

    def __str__(self) -> str:
        return f"FactoryProvider<{self.object_class.__name__}>"

    def _provide(self, args: tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
        # Resolve provider dependencies
        resolved: Dict[str, Any] = {k: v() for k, v in self.dependencies.items()}
        
        # Merge with static arguments
        final_kwargs: Dict[str, Any] = {**self.arguments, **resolved, **kwargs}
        
        try:
            return self.object_class(*args, **final_kwargs)
        except Exception as error:
            raise ProvideObjectError(message=str(error)) from error


class SingletonProvider(FactoryProvider):
    def __init__(self, object_class: Type[Any], **kwargs: Any) -> None:
        super().__init__(object_class, **kwargs)
        self._instance: Optional[Any] = None

    def _provide(self, args: tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
        if self._instance is None:
            try:
                self._instance = super()._provide(args, kwargs)
            except ProvideObjectError:
                # Don't cache failed instances
                raise
        return self._instance
    
    def reset(self) -> None:
        """Reset the singleton instance."""
        self._instance = None
