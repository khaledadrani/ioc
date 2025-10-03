from functools import partial

import pytest

from ioc.exceptions import ProvideObjectError, ProvideObjectAttributeError
from ioc.providers import FactoryProvider
from tests.conftest import DummyDatabase


class TestBasicProvider:
    def setup_method(self):
        self.object_to_provide = DummyDatabase
        self.construct_args = {"connection_string": "db_url"}

        self.bad_construct_args = {"connectionString": "db_url"}

        self.create_provide_object = partial(FactoryProvider, self.object_to_provide, **self.construct_args)
        self.create_provide_object_bad = partial(FactoryProvider, self.object_to_provide, **self.bad_construct_args)

    def test_init_provider(self):
        result = self.create_provide_object()

        assert result.object_class == DummyDatabase
        assert isinstance(result.arguments, dict) and len(result.arguments) == 1
        assert isinstance(result.dependencies, dict) and len(result.dependencies) == 0
        assert callable(result._provide)

    def test_provide_object(self):
        object_provider = self.create_provide_object()

        result = object_provider()

        assert isinstance(result, self.object_to_provide)

    def test_bad_arguments_for_provide(self):
        object_provider = self.create_provide_object_bad()

        with pytest.raises(ProvideObjectError):
            object_provider()

    def test_str_method(self):
        object_provider = self.create_provide_object()

        result = str(object_provider)

        assert isinstance(result, str)

    def test_call(self):
        object_provider = self.create_provide_object()

        result = object_provider()

        assert isinstance(result, self.object_to_provide)

    def test_provider_override_success(self):
        # Arrange
        original_provider = self.create_provide_object()
        override_provider = FactoryProvider(self.object_to_provide, connection_string="override_url")
        
        # Act
        with original_provider.override(override_provider) as override:
            result = original_provider()
        
        # Assert
        assert isinstance(result, self.object_to_provide)
        assert result.connection_string == "override_url"
        assert override == override_provider

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_get_attr(self):
        object_provider = self.create_provide_object()

        result = object_provider.connection_string

        assert result

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_handle_get_attr_error(self):
        object_provider = self.create_provide_object()
        with pytest.raises(ProvideObjectAttributeError):
            _ = object_provider.connection_String
