from __future__ import annotations

from typing import Any, Optional, List


class Provider:
    """Base provider class that all providers must inherit from."""
    
    def __init__(self) -> None:
        self._overridden: List[Provider] = []
        self._last_overriding: Optional[Provider] = None
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Make provider callable."""
        if self._last_overriding:
            return self._last_overriding(*args, **kwargs)
        return self._provide(args, kwargs)
    
    def _provide(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """Override this in subclasses."""
        raise NotImplementedError()
    
    def override(self, provider: Provider) -> OverrideContext:
        """Override this provider with another provider."""
        if not isinstance(provider, Provider):
            raise TypeError("Can only override with Provider instances")
        
        self._overridden.append(provider)
        self._last_overriding = provider
        return OverrideContext(self, provider)
    
    def reset_override(self) -> None:
        """Reset all overrides."""
        self._overridden.clear()
        self._last_overriding = None


class OverrideContext:
    """Context manager for provider overriding."""
    
    def __init__(self, provider: Provider, overriding_provider: Provider) -> None:
        self.provider: Provider = provider
        self.overriding_provider: Provider = overriding_provider
    
    def __enter__(self) -> Provider:
        return self.overriding_provider
    
    def __exit__(self, *args: Any) -> None:
        if self.provider._overridden:
            self.provider._overridden.pop()
            self.provider._last_overriding = (
                self.provider._overridden[-1] if self.provider._overridden else None
            )