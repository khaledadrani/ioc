from __future__ import annotations

from typing import Any, Dict, Callable
from ..exceptions import ProvideObjectError
from .base import Provider
from .configuration import TypedConfigurationOption

class CallableProvider(Provider):
    def __init__(self, callable_obj: Callable[..., Any], **kwargs: Any) -> None:
        super().__init__()
        self.callable_obj: Callable[..., Any] = callable_obj
        self.arguments: Dict[str, Any] = kwargs
        self.dependencies: Dict[str, Provider] = {
            k: v for k, v in self.arguments.items() if isinstance(v, Provider)
        }

    def __str__(self) -> str:
        return f"CallableProvider<{getattr(self.callable_obj, '__name__', str(self.callable_obj))}>"

    def _provide(self, args: tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
        # Resolve provider dependencies
        resolved: Dict[str, Any] = {}
        for k, v in self.dependencies.items():
            resolved_value = v()
            if resolved_value is None:
                # Check if this is a TypedConfigurationOption that returned None
                if isinstance(v, TypedConfigurationOption):
                    from ..exceptions import ConfigurationNotLoadedError
                    raise ConfigurationNotLoadedError(
                        config_key=v._option._name,
                        provider_name=f"CallableProvider<{getattr(self.callable_obj, '__name__', str(self.callable_obj))}>"
                    )
            resolved[k] = resolved_value
        
        # Merge with static arguments
        final_kwargs: Dict[str, Any] = {**self.arguments, **resolved, **kwargs}
        
        try:
            return self.callable_obj(*args, **final_kwargs)
        except Exception as error:
            raise ProvideObjectError(message=str(error)) from error