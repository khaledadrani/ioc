from __future__ import annotations

from typing import Any, Dict, Type
from ..exceptions import ProvideObjectError
from .base import Provider


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