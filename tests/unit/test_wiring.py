"""Tests for automatic dependency injection wiring."""

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch
from ioc.wiring import Provide, inject, _inject_dependencies, _resolve_provider, _set_current_container, _get_current_container
from ioc.container import Container
from ioc import FactoryProvider, SingletonProvider


class TestProvideMarker:
    """Test Provide marker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider_mock = Mock()
    
    def test_provide_creation_success(self):
        """Test Provide marker creation."""
        # Arrange
        provider = self.provider_mock
        
        # Act
        provide = Provide(provider)
        
        # Assert
        assert provide.provider == provider
    
    def test_provide_repr_success(self):
        """Test Provide string representation."""
        # Arrange
        provider = self.provider_mock
        provide = Provide(provider)
        
        # Act
        result = repr(provide)
        
        # Assert
        assert result == f"Provide({provider})"


class TestInjectDecorator:
    """Test inject decorator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.container.set_provider('database', FactoryProvider(lambda: self.db_mock))
    
    def test_inject_decorator_marks_function_success(self):
        """Test that inject decorator marks function as wired."""
        # Act
        @inject
        def test_func():
            pass
        
        # Assert
        assert hasattr(test_func, '__wired__')
        assert test_func.__wired__ is True
    
    def test_inject_without_container_success(self):
        """Test inject decorator when no container is wired."""
        # Arrange
        @inject
        def test_func(db=Provide('database')):
            return db
        
        # Act
        result = test_func()
        
        # Assert
        assert isinstance(result, Provide)
    
    def test_inject_with_container_success(self):
        """Test inject decorator with wired container."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        @inject
        def test_func(db=Provide('database')):
            return db
        
        # Act
        with patch('ioc.wiring._get_current_container', return_value=container):
            result = test_func()
        
        # Assert
        assert result == db_mock
    
    def test_inject_preserves_provided_kwargs_success(self):
        """Test that inject preserves explicitly provided arguments."""
        # Arrange
        container = self.container
        custom_db = Mock()
        
        @inject
        def test_func(db=Provide('database')):
            return db
        
        # Act
        with patch('ioc.wiring._get_current_container', return_value=container):
            result = test_func(db=custom_db)
        
        # Assert
        assert result == custom_db


class TestDependencyInjection:
    """Test dependency injection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.cache_mock = Mock()
        self.container.set_provider('database', FactoryProvider(lambda: self.db_mock))
        self.container.set_provider('cache', SingletonProvider(lambda: self.cache_mock))
    
    def test_inject_dependencies_basic_success(self):
        """Test basic dependency injection."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        def test_func(db=Provide('database')):
            return db
        
        # Act
        result = _inject_dependencies(test_func, container, {})
        
        # Assert
        assert result['db'] == db_mock
    
    def test_inject_dependencies_multiple_success(self):
        """Test injection of multiple dependencies."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        cache_mock = self.cache_mock
        
        def test_func(db=Provide('database'), cache=Provide('cache')):
            return db, cache
        
        # Act
        result = _inject_dependencies(test_func, container, {})
        
        # Assert
        assert result['db'] == db_mock
        assert result['cache'] == cache_mock
    
    def test_inject_dependencies_with_provided_kwargs_success(self):
        """Test that provided kwargs are preserved."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        def test_func(db=Provide('database'), value=None):
            return db, value
        
        # Act
        result = _inject_dependencies(test_func, container, {'value': 'test'})
        
        # Assert
        assert result['db'] == db_mock
        assert result['value'] == 'test'
    
    def test_inject_dependencies_skips_non_provide_success(self):
        """Test that non-Provide parameters are skipped."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        def test_func(db=Provide('database'), value='default'):
            return db, value
        
        # Act
        result = _inject_dependencies(test_func, container, {})
        
        # Assert
        assert result['db'] == db_mock
        assert 'value' not in result


class TestProviderResolution:
    """Test provider resolution logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.container.set_provider('database', FactoryProvider(lambda: self.db_mock))
    
    def test_resolve_string_provider_success(self):
        """Test resolving provider by string path."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        # Act
        result = _resolve_provider(container, 'database')
        
        # Assert
        assert result == db_mock
    
    def test_resolve_direct_provider_success(self):
        """Test resolving direct provider reference."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        provider = container.database
        
        # Act
        result = _resolve_provider(container, provider)
        
        # Assert
        assert result == db_mock


class TestContainerWiring:
    """Test container wiring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.container.set_provider('database', FactoryProvider(lambda: self.db_mock))
    
    def test_wire_sets_current_container_success(self):
        """Test that wire() sets the current container."""
        # Arrange
        container = self.container
        
        # Act & Assert
        with patch('ioc.wiring._set_current_container') as mock_set:
            container.wire()
            mock_set.assert_called_once_with(container)
    
    def test_unwire_clears_container_success(self):
        """Test that unwire() clears the current container."""
        # Arrange
        container = self.container
        
        # Act & Assert
        with patch('ioc.wiring._get_current_container', return_value=container), \
             patch('ioc.wiring._set_current_container') as mock_set:
            container.unwire()
            mock_set.assert_called_once_with(None)
    
    def test_unwire_different_container_no_change(self):
        """Test that unwire() doesn't clear if different container is current."""
        # Arrange
        container = self.container
        other_container = Container()
        
        # Act & Assert
        with patch('ioc.wiring._get_current_container', return_value=other_container), \
             patch('ioc.wiring._set_current_container') as mock_set:
            container.unwire()
            mock_set.assert_not_called()


class TestThreadSafety:
    """Test thread safety with contextvars."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container1 = Container()
        self.container2 = Container()
        
        self.db1_mock = Mock()
        self.db2_mock = Mock()
        self.db1_mock.name = "db1"
        self.db2_mock.name = "db2"
        
        self.container1.set_provider('database', FactoryProvider(lambda: self.db1_mock))
        self.container2.set_provider('database', FactoryProvider(lambda: self.db2_mock))
    
    def test_context_isolation_between_threads_success(self):
        """Test context isolation between threads.
        
        Verifies that each thread maintains its own container context
        without interference from other threads.
        """
        # Arrange
        container1 = self.container1
        container2 = self.container2
        
        results = {}
        
        @inject
        def get_db_name(db=Provide('database')):
            return db.name
        
        def thread1_work():
            """Work function for thread 1."""
            _set_current_container(container1)
            time.sleep(0.1)  # Allow thread 2 to set its container
            results['thread1'] = get_db_name()
        
        def thread2_work():
            """Work function for thread 2."""
            _set_current_container(container2)
            time.sleep(0.1)  # Allow thread 1 to set its container
            results['thread2'] = get_db_name()
        
        # Act
        thread1 = threading.Thread(target=thread1_work)
        thread2 = threading.Thread(target=thread2_work)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Assert
        assert results['thread1'] == "db1"
        assert results['thread2'] == "db2"
    
    def test_no_context_leakage_between_threads_success(self):
        """Test no context leakage between threads.
        
        Verifies that container context set in one thread
        does not leak to other threads.
        """
        # Arrange
        container = self.container1
        
        results = {}
        
        def thread1_work():
            """Set container in thread 1."""
            _set_current_container(container)
            results['thread1_has_container'] = _get_current_container() is not None
        
        def thread2_work():
            """Check if container is available in thread 2 (should be None)."""
            time.sleep(0.1)  # Wait for thread1 to set container
            results['thread2_has_container'] = _get_current_container() is not None
        
        # Act
        thread1 = threading.Thread(target=thread1_work)
        thread2 = threading.Thread(target=thread2_work)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Assert
        assert results['thread1_has_container'] is True
        assert results['thread2_has_container'] is False