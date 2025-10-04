from __future__ import annotations

from typing import Any, Dict, Type, Optional
from ..exceptions import ProvideObjectError
from .factory import FactoryProvider


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