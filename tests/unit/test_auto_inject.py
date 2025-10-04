"""Tests for convention-based dependency injection."""

import pytest
import threading
import time
from unittest.mock import Mock
from ioc.wiring import auto_inject, _inject_by_convention, _set_current_container, _get_current_container
from ioc.container import Container
from ioc.providers import FactoryProvider, SingletonProvider
from ioc.exceptions import ConventionInjectionError


class TestAutoInjectDecorator:
    """Test auto_inject decorator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.cache_mock = Mock()
        self.container.set_provider('user_repository', FactoryProvider(lambda: self.db_mock))
        self.container.set_provider('cache_service', SingletonProvider(lambda: self.cache_mock))
    
    def test_auto_inject_decorator_marks_function_success(self):
        """Test that auto_inject decorator marks function as auto_wired."""
        # Act
        @auto_inject
        def test_func():
            pass
        
        # Assert
        assert hasattr(test_func, '__auto_wired__')
        assert test_func.__auto_wired__ is True
    
    def test_auto_inject_without_container_success(self):
        """Test auto_inject decorator when no container is wired."""
        # Arrange
        @auto_inject
        def test_func(user_repository=None):
            return user_repository
        
        # Act
        result = test_func()
        
        # Assert
        assert result is None  # No injection occurred
    
    def test_auto_inject_with_container_success(self):
        """Test auto_inject decorator with wired container."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        @auto_inject
        def test_func(user_repository: Mock):
            return user_repository
        
        # Act
        _set_current_container(container)
        result = test_func()
        
        # Assert
        assert result == db_mock
    
    def test_auto_inject_preserves_provided_kwargs_success(self):
        """Test that auto_inject preserves explicitly provided arguments."""
        # Arrange
        container = self.container
        custom_repo = Mock()
        
        @auto_inject
        def test_func(user_repository: Mock):
            return user_repository
        
        # Act
        _set_current_container(container)
        result = test_func(user_repository=custom_repo)
        
        # Assert
        assert result == custom_repo


class TestConventionInjection:
    """Test convention-based injection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.cache_mock = Mock()
        self.container.set_provider('user_repository', FactoryProvider(lambda: self.db_mock))
        self.container.set_provider('cache_service', SingletonProvider(lambda: self.cache_mock))
    
    def test_inject_by_convention_basic_success(self):
        """Test basic convention-based injection."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        def test_func(user_repository: Mock):
            return user_repository
        
        # Act
        result = _inject_by_convention(test_func, container, {})
        
        # Assert
        assert result['user_repository'] == db_mock
    
    def test_inject_by_convention_multiple_success(self):
        """Test injection of multiple dependencies by convention."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        cache_mock = self.cache_mock
        
        def test_func(user_repository: Mock, cache_service: Mock):
            return user_repository, cache_service
        
        # Act
        result = _inject_by_convention(test_func, container, {})
        
        # Assert
        assert result['user_repository'] == db_mock
        assert result['cache_service'] == cache_mock
    
    def test_inject_by_convention_with_provided_kwargs_success(self):
        """Test that provided kwargs are preserved."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        def test_func(user_repository: Mock, value):
            return user_repository, value
        
        # Act
        result = _inject_by_convention(test_func, container, {'value': 'test'})
        
        # Assert
        assert result['user_repository'] == db_mock
        assert result['value'] == 'test'
    
    def test_inject_by_convention_skips_non_matching_success(self):
        """Test that non-matching parameters with defaults are skipped."""
        # Arrange
        container = self.container
        db_mock = self.db_mock
        
        def test_func(user_repository: Mock, value='default'):
            return user_repository, value
        
        # Act
        result = _inject_by_convention(test_func, container, {})
        
        # Assert
        assert result['user_repository'] == db_mock
        assert 'value' not in result


class TestConventionInjectionErrors:
    """Test convention-based injection error cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        self.db_mock = Mock()
        self.container.set_provider('user_repository', FactoryProvider(lambda: self.db_mock))
    
    def test_inject_by_convention_missing_provider_no_error(self):
        """Test that missing provider with default doesn't raise error."""
        # Arrange
        container = self.container
        
        def test_func(missing_service=None):
            return missing_service
        
        # Act
        result = _inject_by_convention(test_func, container, {})
        
        # Assert - no injection occurred, parameter not in result
        assert 'missing_service' not in result
    
    def test_inject_by_convention_non_callable_provider_error(self):
        """Test error when provider is not callable."""
        # Arrange
        container = self.container
        container.non_callable = "not a provider"
        
        def test_func(non_callable: str):
            return non_callable
        
        # Act & Assert
        with pytest.raises(ConventionInjectionError) as exc_info:
            _inject_by_convention(test_func, container, {})
        
        assert "'non_callable' is not a callable provider" in str(exc_info.value)
    
    def test_inject_by_convention_type_mismatch_error(self):
        """Test error when injected type doesn't match annotation."""
        # Arrange
        container = self.container
        
        def test_func(user_repository: str):  # Wrong type annotation
            return user_repository
        
        # Act & Assert
        with pytest.raises(ConventionInjectionError) as exc_info:
            _inject_by_convention(test_func, container, {})
        
        assert "Parameter 'user_repository' expects str, got" in str(exc_info.value)
    
    def test_inject_by_convention_missing_annotation_error(self):
        """Test error when injected parameter has no type annotation."""
        # Arrange
        container = self.container
        
        def test_func(user_repository):  # No type annotation
            return user_repository
        
        # Act & Assert
        with pytest.raises(ConventionInjectionError) as exc_info:
            _inject_by_convention(test_func, container, {})
        
        assert "Parameter 'user_repository' requires type annotation for auto-injection" in str(exc_info.value)


class TestConventionInjectionIntegration:
    """Test convention-based injection integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container = Container()
        
        # Create mock services
        self.db_mock = Mock()
        self.email_mock = Mock()
        self.db_mock.get_user.return_value = "User 123"
        self.email_mock.send_welcome.return_value = "Email sent"
        
        # Setup container with convention-friendly names
        self.container.set_provider('user_repository', FactoryProvider(lambda: self.db_mock))
        self.container.set_provider('email_service', FactoryProvider(lambda: self.email_mock))
    
    def test_convention_injection_full_workflow_success(self):
        """Test complete convention-based injection workflow."""
        # Arrange
        container = self.container
        
        @auto_inject
        def get_user_info(user_id: int, user_repository: Mock):
            return user_repository.get_user(user_id)
        
        @auto_inject
        def welcome_user(user_id: int, user_repository: Mock, email_service: Mock):
            user = user_repository.get_user(user_id)
            return email_service.send_welcome(user)
        
        # Act
        _set_current_container(container)
        user_info = get_user_info(123)
        welcome_msg = welcome_user(456)
        
        # Assert
        assert user_info == "User 123"
        assert welcome_msg == "Email sent"
        self.db_mock.get_user.assert_called_with(456)  # Last call
        self.email_mock.send_welcome.assert_called_once_with("User 123")


class TestConventionInjectionThreadSafety:
    """Test convention-based injection thread safety."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.container1 = Container()
        self.container2 = Container()
        
        self.db1_mock = Mock()
        self.db2_mock = Mock()
        self.db1_mock.name = "db1"
        self.db2_mock.name = "db2"
        
        self.container1.set_provider('user_repository', FactoryProvider(lambda: self.db1_mock))
        self.container2.set_provider('user_repository', FactoryProvider(lambda: self.db2_mock))
    
    def test_convention_injection_thread_isolation_success(self):
        """Test that convention injection works correctly across threads."""
        # Arrange
        results = {}
        
        @auto_inject
        def get_db_name(user_repository: Mock):
            return user_repository.name
        
        def thread1_work():
            """Work function for thread 1."""
            _set_current_container(self.container1)
            time.sleep(0.1)  # Allow thread 2 to set its container
            results['thread1'] = get_db_name()
        
        def thread2_work():
            """Work function for thread 2."""
            _set_current_container(self.container2)
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