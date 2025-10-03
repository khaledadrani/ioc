import pytest
from unittest.mock import MagicMock

from ioc.base_provider import Provider, OverrideContext
from ioc.exceptions import ProvideObjectError


class MockProvider(Provider):
    """Mock provider for testing base functionality."""
    
    def __init__(self, return_value="mock_result"):
        super().__init__()
        self.return_value = return_value
    
    def _provide(self, args, kwargs):
        return self.return_value


class TestProvider:
    def setup_method(self):
        self.provider = MockProvider("test_result")
        self.override_provider = MockProvider("override_result")

    def test_provider_call_success(self):
        # Act
        result = self.provider()
        
        # Assert
        assert result == "test_result"

    def test_provider_call_with_args_kwargs(self):
        # Arrange
        provider = MockProvider()
        provider._provide = MagicMock(return_value="result_with_args")
        
        # Act
        result = provider("arg1", "arg2", key1="value1", key2="value2")
        
        # Assert
        assert result == "result_with_args"
        provider._provide.assert_called_once_with(("arg1", "arg2"), {"key1": "value1", "key2": "value2"})

    def test_provider_abstract_provide_raises_not_implemented(self):
        # Arrange
        abstract_provider = Provider()
        
        # Act & Assert
        with pytest.raises(NotImplementedError):
            abstract_provider._provide((), {})

    def test_override_success(self):
        # Act
        context = self.provider.override(self.override_provider)
        
        # Assert
        assert isinstance(context, OverrideContext)
        assert self.provider._last_overriding == self.override_provider
        assert self.override_provider in self.provider._overridden

    def test_override_invalid_type_raises_error(self):
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            self.provider.override("not_a_provider")
        
        assert "Can only override with Provider instances" in str(exc_info.value)

    def test_overridden_provider_call_returns_override_result(self):
        # Arrange
        self.provider.override(self.override_provider)
        
        # Act
        result = self.provider()
        
        # Assert
        assert result == "override_result"

    def test_reset_override_success(self):
        # Arrange
        self.provider.override(self.override_provider)
        
        # Act
        self.provider.reset_override()
        
        # Assert
        assert self.provider._last_overriding is None
        assert len(self.provider._overridden) == 0

    def test_multiple_overrides_uses_last_override(self):
        # Arrange
        second_override = MockProvider("second_override")
        self.provider.override(self.override_provider)
        self.provider.override(second_override)
        
        # Act
        result = self.provider()
        
        # Assert
        assert result == "second_override"
        assert self.provider._last_overriding == second_override


class TestOverrideContext:
    def setup_method(self):
        self.provider = MockProvider("original")
        self.override_provider = MockProvider("override")

    def test_context_manager_enter_returns_override_provider(self):
        # Arrange
        context = OverrideContext(self.provider, self.override_provider)
        
        # Act
        with context as override:
            # Assert
            assert override == self.override_provider

    def test_context_manager_exit_removes_last_override(self):
        # Arrange
        self.provider.override(self.override_provider)
        context = OverrideContext(self.provider, self.override_provider)
        
        # Act
        with context:
            assert self.provider._last_overriding == self.override_provider
        
        # Assert
        assert self.provider._last_overriding is None
        assert len(self.provider._overridden) == 0

    def test_context_manager_with_multiple_overrides(self):
        # Arrange
        first_override = MockProvider("first")
        second_override = MockProvider("second")
        
        self.provider.override(first_override)
        self.provider.override(second_override)
        
        context = OverrideContext(self.provider, second_override)
        
        # Act
        with context:
            assert self.provider._last_overriding == second_override
        
        # Assert - Should revert to first override
        assert self.provider._last_overriding == first_override
        assert len(self.provider._overridden) == 1

    def test_context_manager_usage_pattern(self):
        # Arrange & Act
        with self.provider.override(self.override_provider) as override:
            result_during_override = self.provider()
            assert override == self.override_provider
        
        result_after_override = self.provider()
        
        # Assert
        assert result_during_override == "override"
        assert result_after_override == "original"