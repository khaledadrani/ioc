import pytest
from functools import partial

from ioc import CallableProvider, FactoryProvider, Provider
from ioc.exceptions import ProvideObjectError


def sample_function(x, y=10):
    """Sample function for testing."""
    return x + y


def function_with_kwargs(name, greeting="Hello", punctuation="!"):
    """Function that uses keyword arguments."""
    return f"{greeting} {name}{punctuation}"


def function_that_raises(should_raise=False):
    """Function that can raise an exception."""
    if should_raise:
        raise ValueError("Test error")
    return "success"


class TestCallableProvider:
    def setup_method(self):
        self.sample_callable = sample_function
        self.create_callable_provider = partial(CallableProvider, self.sample_callable)

    def test_callable_provider_inherits_from_provider(self):
        # Arrange & Act
        provider = self.create_callable_provider()
        
        # Assert
        assert isinstance(provider, Provider)

    def test_init_callable_provider(self):
        # Arrange & Act
        provider = self.create_callable_provider(y=20)
        
        # Assert
        assert provider.callable_obj == sample_function
        assert provider.arguments == {"y": 20}
        assert provider.dependencies == {}

    def test_init_callable_provider_with_provider_dependencies(self):
        # Arrange
        class IntWrapper:
            def __init__(self, value):
                self.value = value
            def __call__(self):
                return self.value
        
        dependency_provider = FactoryProvider(IntWrapper, value=42)
        
        # Act
        provider = CallableProvider(sample_function, y=dependency_provider)
        
        # Assert
        assert provider.callable_obj == sample_function
        assert provider.arguments == {"y": dependency_provider}
        assert provider.dependencies == {"y": dependency_provider}

    def test_str_method(self):
        # Arrange
        provider = self.create_callable_provider()
        
        # Act
        result = str(provider)
        
        # Assert
        assert result == "CallableProvider<sample_function>"

    def test_str_method_with_unnamed_callable(self):
        # Arrange
        lambda_func = lambda x: x * 2
        provider = CallableProvider(lambda_func)
        
        # Act
        result = str(provider)
        
        # Assert
        assert "CallableProvider<" in result
        assert "lambda" in result

    def test_provide_function_with_no_args(self):
        # Arrange
        provider = self.create_callable_provider()
        
        # Act
        result = provider(5)
        
        # Assert
        assert result == 15  # 5 + 10 (default y)

    def test_provide_function_with_static_args(self):
        # Arrange
        provider = CallableProvider(sample_function, y=20)
        
        # Act
        result = provider(5)
        
        # Assert
        assert result == 25  # 5 + 20

    def test_provide_function_with_runtime_kwargs(self):
        # Arrange
        provider = self.create_callable_provider()
        
        # Act
        result = provider(5, y=30)
        
        # Assert
        assert result == 35  # 5 + 30

    def test_provide_function_runtime_kwargs_override_static(self):
        # Arrange
        provider = CallableProvider(sample_function, y=20)
        
        # Act
        result = provider(5, y=30)
        
        # Assert
        assert result == 35  # Runtime kwargs override static

    def test_provide_function_with_provider_dependencies(self):
        # Arrange
        class ValueProvider:
            def __init__(self, value):
                self.value = value
        
        y_provider = FactoryProvider(ValueProvider, value=25)
        
        def add_with_provider(x, y):
            return x + y.value
        
        provider = CallableProvider(add_with_provider, y=y_provider)
        
        # Act
        result = provider(5)
        
        # Assert
        assert result == 30  # 5 + 25

    def test_provide_function_complex_kwargs(self):
        # Arrange
        provider = CallableProvider(function_with_kwargs, greeting="Hi")
        
        # Act
        result = provider("World", punctuation=".")
        
        # Assert
        assert result == "Hi World."

    def test_provide_function_with_mixed_dependencies(self):
        # Arrange
        class StringProvider:
            def __init__(self, value):
                self.value = value
        
        greeting_provider = FactoryProvider(StringProvider, value="Hey")
        
        def format_with_provider(name, greeting, punctuation="!"):
            return f"{greeting.value} {name}{punctuation}"
        
        provider = CallableProvider(
            format_with_provider, 
            greeting=greeting_provider,
            punctuation="!!!"
        )
        
        # Act
        result = provider("Alice")
        
        # Assert
        assert result == "Hey Alice!!!"

    def test_call_method_delegates_to_provide(self):
        # Arrange
        provider = self.create_callable_provider()
        
        # Act
        result = provider(7)
        
        # Assert
        assert result == 17  # 7 + 10

    def test_provider_override_success(self):
        # Arrange
        original_provider = CallableProvider(sample_function, y=10)
        override_provider = CallableProvider(sample_function, y=100)
        
        # Act
        with original_provider.override(override_provider):
            result = original_provider(5)
        
        # Assert
        assert result == 105  # 5 + 100

    def test_provider_override_context_manager(self):
        # Arrange
        original_provider = CallableProvider(sample_function, y=10)
        override_provider = CallableProvider(sample_function, y=100)
        
        # Act & Assert
        # Before override
        assert original_provider(5) == 15
        
        # During override
        with original_provider.override(override_provider) as override:
            assert original_provider(5) == 105
            assert override == override_provider
        
        # After override
        assert original_provider(5) == 15

    def test_provide_function_exception_handling(self):
        # Arrange
        provider = CallableProvider(function_that_raises, should_raise=True)
        
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            provider()
        
        assert "Test error" in str(exc_info.value)

    def test_provide_function_exception_preserves_original(self):
        # Arrange
        provider = CallableProvider(function_that_raises, should_raise=True)
        
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            provider()
        
        # Check that original exception is preserved
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_provide_function_success_after_exception(self):
        # Arrange
        provider = CallableProvider(function_that_raises)
        
        # Act
        result = provider(should_raise=False)
        
        # Assert
        assert result == "success"

    def test_callable_provider_with_method(self):
        # Arrange
        class TestClass:
            def __init__(self, multiplier):
                self.multiplier = multiplier
            
            def multiply(self, value):
                return value * self.multiplier
        
        test_obj = TestClass(3)
        provider = CallableProvider(test_obj.multiply)
        
        # Act
        result = provider(4)
        
        # Assert
        assert result == 12

    def test_callable_provider_with_builtin_function(self):
        # Arrange
        provider = CallableProvider(len)
        
        # Act
        result = provider([1, 2, 3, 4])
        
        # Assert
        assert result == 4

    def test_callable_provider_with_lambda(self):
        # Arrange
        square = lambda x: x ** 2
        provider = CallableProvider(square)
        
        # Act
        result = provider(5)
        
        # Assert
        assert result == 25

    def test_nested_provider_dependencies(self):
        # Arrange
        class NumberProvider:
            def __init__(self, value):
                self.value = value
        
        base_provider = FactoryProvider(NumberProvider, value=10)
        multiplier_provider = FactoryProvider(NumberProvider, value=3)
        
        def multiply_and_add(x, base, multiplier):
            return (x * multiplier.value) + base.value
        
        provider = CallableProvider(
            multiply_and_add,
            base=base_provider,
            multiplier=multiplier_provider
        )
        
        # Act
        result = provider(5)
        
        # Assert
        assert result == 25  # (5 * 3) + 10

    def test_provider_dependencies_resolved_each_call(self):
        # Arrange
        counter = 0
        
        def increment():
            nonlocal counter
            counter += 1
            return counter
        
        counter_provider = CallableProvider(increment)
        
        def add_counter(x, count):
            return x + count
        
        provider = CallableProvider(add_counter, count=counter_provider)
        
        # Act
        result1 = provider(10)
        result2 = provider(10)
        
        # Assert
        assert result1 == 11  # 10 + 1
        assert result2 == 12  # 10 + 2 (counter incremented)