import pytest
from unittest.mock import MagicMock, patch

from inject.providers import FactoryProvider, SingletonProvider
from inject.base_provider import Provider
from inject.exceptions import ProvideObjectError
from tests.conftest import DummyDatabase, DummyRepository, DummyService


class TestFactoryProvider:
    def setup_method(self):
        self.object_class = DummyDatabase
        self.connection_string = "test://db"
        self.provider = FactoryProvider(self.object_class, connection_string=self.connection_string)

    def test_factory_provider_inherits_from_provider(self):
        # Assert
        assert isinstance(self.provider, Provider)

    def test_factory_provider_initialization_success(self):
        # Assert
        assert self.provider.object_class == self.object_class
        assert self.provider.arguments["connection_string"] == self.connection_string
        assert len(self.provider.dependencies) == 0

    def test_factory_provider_with_provider_dependencies(self):
        # Arrange
        db_provider = FactoryProvider(DummyDatabase, connection_string="db://test")
        repo_provider = FactoryProvider(DummyRepository, db=db_provider)
        
        # Assert
        assert "db" in repo_provider.dependencies
        assert repo_provider.dependencies["db"] == db_provider

    def test_factory_provider_call_success(self):
        # Act
        result = self.provider()
        
        # Assert
        assert isinstance(result, DummyDatabase)
        assert result.connection_string == self.connection_string

    def test_factory_provider_call_with_runtime_args(self):
        # Arrange
        provider = FactoryProvider(DummyDatabase)
        
        # Act
        result = provider(connection_string="runtime://db")
        
        # Assert
        assert isinstance(result, DummyDatabase)
        assert result.connection_string == "runtime://db"

    def test_factory_provider_call_with_provider_dependencies(self):
        # Arrange
        db_provider = FactoryProvider(DummyDatabase, connection_string="db://test")
        repo_provider = FactoryProvider(DummyRepository, db=db_provider)
        
        # Act
        result = repo_provider()
        
        # Assert
        assert isinstance(result, DummyRepository)
        assert isinstance(result.db, DummyDatabase)
        assert result.db.connection_string == "db://test"

    def test_factory_provider_call_invalid_arguments_raises_error(self):
        # Arrange
        provider = FactoryProvider(DummyDatabase, invalid_arg="value")
        
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            provider()
        
        assert "unexpected keyword argument" in str(exc_info.value)

    def test_factory_provider_str_representation(self):
        # Act
        result = str(self.provider)
        
        # Assert
        assert result == "FactoryProvider<DummyDatabase>"

    def test_factory_provider_override_success(self):
        # Arrange
        override_provider = FactoryProvider(DummyDatabase, connection_string="override://db")
        
        # Act
        with self.provider.override(override_provider):
            result = self.provider()
        
        # Assert
        assert result.connection_string == "override://db"

    def test_factory_provider_complex_dependency_chain(self):
        # Arrange
        db_provider = FactoryProvider(DummyDatabase, connection_string="chain://db")
        repo_provider = FactoryProvider(DummyRepository, db=db_provider)
        service_provider = FactoryProvider(DummyService, repository=repo_provider)
        
        # Act
        result = service_provider()
        
        # Assert
        assert isinstance(result, DummyService)
        assert isinstance(result.repository, DummyRepository)
        assert isinstance(result.repository.db, DummyDatabase)
        assert result.repository.db.connection_string == "chain://db"

    def test_factory_provider_runtime_kwargs_override_static(self):
        # Arrange
        provider = FactoryProvider(DummyDatabase, connection_string="static://db")
        
        # Act
        result = provider(connection_string="runtime://db")
        
        # Assert
        assert result.connection_string == "runtime://db"


class TestSingletonProvider:
    def setup_method(self):
        self.object_class = DummyDatabase
        self.connection_string = "singleton://db"
        self.provider = SingletonProvider(self.object_class, connection_string=self.connection_string)

    def test_singleton_provider_inherits_from_factory_provider(self):
        # Assert
        assert isinstance(self.provider, FactoryProvider)
        assert isinstance(self.provider, Provider)

    def test_singleton_provider_initialization_success(self):
        # Assert
        assert self.provider.object_class == self.object_class
        assert self.provider.arguments["connection_string"] == self.connection_string
        assert self.provider._instance is None

    def test_singleton_provider_returns_same_instance(self):
        # Act
        first_instance = self.provider()
        second_instance = self.provider()
        
        # Assert
        assert first_instance is second_instance
        assert id(first_instance) == id(second_instance)

    def test_singleton_provider_creates_instance_once(self):
        # Arrange
        mock_class = MagicMock(return_value="singleton_instance")
        provider = SingletonProvider(mock_class, arg="value")
        
        # Act
        first_call = provider()
        second_call = provider()
        
        # Assert
        assert first_call == second_call
        mock_class.assert_called_once_with(arg="value")

    def test_singleton_provider_reset_clears_instance(self):
        # Arrange
        first_instance = self.provider()
        
        # Act
        self.provider.reset()
        second_instance = self.provider()
        
        # Assert
        assert first_instance is not second_instance
        assert self.provider._instance == second_instance

    def test_singleton_provider_with_dependencies(self):
        # Arrange
        db_provider = SingletonProvider(DummyDatabase, connection_string="singleton://db")
        repo_provider = SingletonProvider(DummyRepository, db=db_provider)
        
        # Act
        first_repo = repo_provider()
        second_repo = repo_provider()
        
        # Assert
        assert first_repo is second_repo
        assert first_repo.db is second_repo.db

    def test_singleton_provider_override_affects_singleton(self):
        # Arrange
        override_provider = FactoryProvider(DummyDatabase, connection_string="override://db")
        original_instance = self.provider()
        
        # Act
        with self.provider.override(override_provider):
            override_instance = self.provider()
        
        after_override_instance = self.provider()
        
        # Assert
        assert override_instance.connection_string == "override://db"
        assert after_override_instance is original_instance

    def test_singleton_provider_str_representation(self):
        # Act
        result = str(self.provider)
        
        # Assert
        assert result == "FactoryProvider<DummyDatabase>"

    def test_singleton_provider_exception_during_creation_raises_error(self):
        # Arrange
        def failing_class():
            raise ValueError("Creation failed")
        
        provider = SingletonProvider(failing_class)
        
        # Act & Assert
        with pytest.raises(ProvideObjectError):
            provider()
        
        # Verify instance is not cached on failure
        assert provider._instance is None

    def test_singleton_provider_reset_after_exception_allows_retry(self):
        # Arrange
        call_count = 0
        
        def sometimes_failing_class():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return f"success_instance_{call_count}"
        
        provider = SingletonProvider(sometimes_failing_class)
        
        # Act
        with pytest.raises(ProvideObjectError):
            provider()
        
        provider.reset()
        result = provider()
        
        # Assert
        assert result == "success_instance_2"
        assert provider._instance == result