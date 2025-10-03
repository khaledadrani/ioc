import pytest
from unittest.mock import MagicMock

from inject.container import Container, ContainerOverrideContext, BaseContainer
from inject.providers import FactoryProvider, SingletonProvider
from inject.base_provider import Provider
from tests.conftest import DummyDatabase, DummyRepository, DummyService


class MockProvider(Provider):
    """Mock provider for testing."""
    
    def __init__(self, return_value="mock"):
        super().__init__()
        self.return_value = return_value
    
    def _provide(self, args, kwargs):
        return self.return_value


class TestContainer:
    def setup_method(self):
        self.container = Container()
        self.mock_provider = MockProvider("test_value")

    def test_container_initialization_success(self):
        # Assert
        assert isinstance(self.container.providers, dict)
        assert len(self.container.providers) == 0
        assert isinstance(self.container._overridden, list)

    def test_set_provider_success(self):
        # Act
        self.container.set_provider("test", self.mock_provider)
        
        # Assert
        assert "test" in self.container.providers
        assert self.container.providers["test"] == self.mock_provider
        assert hasattr(self.container, "test")
        assert self.container.test == self.mock_provider

    def test_set_provider_invalid_type_raises_error(self):
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            self.container.set_provider("test", "not_a_provider")
        
        assert "Only Provider instances can be registered" in str(exc_info.value)

    def test_setattr_provider_auto_registration(self):
        # Act
        self.container.database = self.mock_provider
        
        # Assert
        assert "database" in self.container.providers
        assert self.container.providers["database"] == self.mock_provider

    def test_setattr_non_provider_not_registered(self):
        # Act
        self.container.config = "some_config"
        
        # Assert
        assert "config" not in self.container.providers
        assert self.container.config == "some_config"

    def test_setattr_private_attribute_not_registered(self):
        # Act
        self.container._private = self.mock_provider
        
        # Assert
        assert "_private" not in self.container.providers
        assert self.container._private == self.mock_provider

    def test_getattr_existing_provider_success(self):
        # Arrange
        self.container.set_provider("test", self.mock_provider)
        
        # Act
        result = self.container.test
        
        # Assert
        assert result == self.mock_provider

    def test_getattr_nonexistent_provider_raises_error(self):
        # Act & Assert
        with pytest.raises(AttributeError) as exc_info:
            _ = self.container.nonexistent
        
        assert "Container has no provider 'nonexistent'" in str(exc_info.value)

    def test_override_providers_success(self):
        # Arrange
        original_provider = MockProvider("original")
        override_provider = MockProvider("override")
        self.container.set_provider("test", original_provider)
        
        # Act
        context = self.container.override_providers(test=override_provider)
        
        # Assert
        assert isinstance(context, ContainerOverrideContext)
        assert original_provider._last_overriding == override_provider

    def test_override_providers_nonexistent_provider_ignored(self):
        # Arrange
        override_provider = MockProvider("override")
        
        # Act
        context = self.container.override_providers(nonexistent=override_provider)
        
        # Assert
        assert isinstance(context, ContainerOverrideContext)
        assert len(context.overridden_providers) == 0

    def test_reset_overrides_success(self):
        # Arrange
        provider1 = MockProvider("original1")
        provider2 = MockProvider("original2")
        override1 = MockProvider("override1")
        override2 = MockProvider("override2")
        
        self.container.set_provider("test1", provider1)
        self.container.set_provider("test2", provider2)
        
        provider1.override(override1)
        provider2.override(override2)
        
        # Act
        self.container.reset_overrides()
        
        # Assert
        assert provider1._last_overriding is None
        assert provider2._last_overriding is None

    def test_wire_placeholder_method_exists(self):
        # Act & Assert - Should not raise error
        self.container.wire()
        self.container.wire(modules=["test"])

    def test_container_with_real_providers(self):
        # Arrange
        db_provider = SingletonProvider(DummyDatabase, connection_string="test://db")
        repo_provider = FactoryProvider(DummyRepository, db=db_provider)
        
        # Act
        self.container.database = db_provider
        self.container.repository = repo_provider
        
        # Assert
        assert len(self.container.providers) == 2
        repo = self.container.repository()
        assert isinstance(repo, DummyRepository)
        assert isinstance(repo.db, DummyDatabase)


class TestContainerOverrideContext:
    def setup_method(self):
        self.container = Container()
        self.provider1 = MockProvider("original1")
        self.provider2 = MockProvider("original2")
        self.override1 = MockProvider("override1")
        self.override2 = MockProvider("override2")
        
        self.container.set_provider("test1", self.provider1)
        self.container.set_provider("test2", self.provider2)

    def test_context_manager_enter_returns_container(self):
        # Arrange
        context = ContainerOverrideContext(self.container, [self.provider1])
        
        # Act
        with context as container:
            # Assert
            assert container == self.container

    def test_context_manager_exit_resets_overrides(self):
        # Arrange
        self.provider1.override(self.override1)
        self.provider2.override(self.override2)
        
        context = ContainerOverrideContext(self.container, [self.provider1, self.provider2])
        
        # Act
        with context:
            assert self.provider1._last_overriding == self.override1
            assert self.provider2._last_overriding == self.override2
        
        # Assert
        assert self.provider1._last_overriding is None
        assert self.provider2._last_overriding is None

    def test_context_manager_usage_pattern(self):
        # Arrange & Act
        with self.container.override_providers(test1=self.override1) as container:
            result_during_override = container.test1()
            assert container == self.container
        
        result_after_override = self.container.test1()
        
        # Assert
        assert result_during_override == "override1"
        assert result_after_override == "original1"


class TestDeclarativeContainer:
    def test_declarative_container_creation(self):
        # Arrange & Act
        class TestContainer(BaseContainer):
            database = SingletonProvider(DummyDatabase, connection_string="declarative://db")
            repository = FactoryProvider(DummyRepository, db=database)
        
        # Assert
        assert hasattr(TestContainer, '_class_providers')
        assert len(TestContainer._class_providers) == 2
        assert 'database' in TestContainer._class_providers
        assert 'repository' in TestContainer._class_providers

    def test_declarative_container_instantiation(self):
        # Arrange
        class TestContainer(BaseContainer):
            database = SingletonProvider(DummyDatabase, connection_string="test://db")
            repository = FactoryProvider(DummyRepository, db=database)
        
        # Act
        container = TestContainer()
        
        # Assert
        assert isinstance(container, Container)
        assert len(container.providers) == 2
        assert hasattr(container, 'database')
        assert hasattr(container, 'repository')

    def test_declarative_container_with_overrides(self):
        # Arrange
        class TestContainer(BaseContainer):
            database = SingletonProvider(DummyDatabase, connection_string="original://db")
        
        override_db = SingletonProvider(DummyDatabase, connection_string="override://db")
        
        # Act
        container = TestContainer(database=override_db)
        
        # Assert
        db = container.database()
        assert db.connection_string == "override://db"

    def test_declarative_container_inheritance(self):
        # Arrange
        class BaseTestContainer(BaseContainer):
            database = SingletonProvider(DummyDatabase, connection_string="base://db")
        
        class ExtendedContainer(BaseTestContainer):
            repository = FactoryProvider(DummyRepository, db=BaseTestContainer.database)
        
        # Act
        container = ExtendedContainer()
        
        # Assert - Both inherited and own providers
        assert len(container.providers) == 2  # database (inherited) + repository (own)
        repo = container.repository()
        assert isinstance(repo.db, DummyDatabase)
        assert repo.db.connection_string == "base://db"

    def test_declarative_container_no_providers(self):
        # Arrange & Act
        class EmptyContainer(BaseContainer):
            config = "not_a_provider"
        
        container = EmptyContainer()
        
        # Assert
        assert len(container.providers) == 0
        assert not hasattr(container, 'config')

    def test_declarative_container_complex_dependencies(self):
        # Arrange
        class AppContainer(BaseContainer):
            database = SingletonProvider(DummyDatabase, connection_string="app://db")
            repository = SingletonProvider(DummyRepository, db=database)
            service = FactoryProvider(DummyService, repository=repository)
        
        # Act
        container = AppContainer()
        service = container.service()
        
        # Assert
        result = service.get_upper_case("test")
        assert "app://db: TEST" in result

    def test_declarative_container_override_context_manager(self):
        # Arrange
        class AppContainer(BaseContainer):
            database = SingletonProvider(DummyDatabase, connection_string="prod://db")
            repository = FactoryProvider(DummyRepository, db=database)
        
        test_db = SingletonProvider(DummyDatabase, connection_string="test://db")
        container = AppContainer()
        
        # Act
        original_repo = container.repository()
        
        with container.override_providers(database=test_db):
            test_repo = container.repository()
        
        after_repo = container.repository()
        
        # Assert
        assert original_repo.db.connection_string == "prod://db"
        assert test_repo.db.connection_string == "test://db"
        assert after_repo.db.connection_string == "prod://db"


class TestBaseContainer:
    def test_base_container_is_abstract(self):
        # Act
        container = BaseContainer()
        
        # Assert
        assert isinstance(container, Container)
        assert len(container.providers) == 0

    def test_base_container_metaclass_applied(self):
        # Assert
        assert hasattr(BaseContainer, '_class_providers')
        assert isinstance(BaseContainer._class_providers, dict)