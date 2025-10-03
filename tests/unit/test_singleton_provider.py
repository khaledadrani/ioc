from functools import partial

from inject.providers import SingletonProvider
from tests.conftest import DummyDatabase


class TestSingletonProvider:
    def setup_method(self):
        self.object_to_provide = DummyDatabase
        self.construct_args = {"connection_string": "db_url"}
        self.create_provide_object = partial(SingletonProvider, self.object_to_provide, **self.construct_args)

    def test_singleton_provide(self):
        provider = self.create_provide_object()

        first_object = provider()
        second_object = provider()

        assert id(first_object) == id(second_object)

    def test_singleton_reset_creates_new_instance(self):
        # Arrange
        provider = self.create_provide_object()
        first_instance = provider()
        
        # Act
        provider.reset()
        second_instance = provider()
        
        # Assert
        assert id(first_instance) != id(second_instance)
        assert isinstance(first_instance, self.object_to_provide)
        assert isinstance(second_instance, self.object_to_provide)

    def test_singleton_override_with_context_manager(self):
        # Arrange
        provider = self.create_provide_object()
        override_provider = SingletonProvider(self.object_to_provide, connection_string="override_db")
        
        original_instance = provider()
        
        # Act
        with provider.override(override_provider):
            override_instance = provider()
        
        after_override_instance = provider()
        
        # Assert
        assert override_instance.connection_string == "override_db"
        assert after_override_instance is original_instance
        assert override_instance is not original_instance
