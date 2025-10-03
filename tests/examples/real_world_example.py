#!/usr/bin/env python3
"""Real-world example using Configuration provider with a complete application setup."""

import os
from ioc.config_provider import ConfigurationProvider
from ioc.providers import FactoryProvider, SingletonProvider
from ioc.container import BaseContainer


# Application classes
class DatabaseConnection:
    def __init__(self, host, port, database, username, password):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def connect(self):
        return f"Connected to {self.connection_string}"


class CacheService:
    def __init__(self, host, port, ttl=3600):
        self.host = host
        self.port = port
        self.ttl = ttl
    
    def get(self, key):
        return f"Cache get {key} from {self.host}:{self.port}"
    
    def set(self, key, value):
        return f"Cache set {key}={value} (TTL: {self.ttl}s)"


class EmailService:
    def __init__(self, smtp_host, smtp_port, username, password, from_email):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
    
    def send_email(self, to, subject, body):
        return f"Email sent from {self.from_email} to {to}: {subject}"


class UserRepository:
    def __init__(self, database, cache=None):
        self.database = database
        self.cache = cache
    
    def get_user(self, user_id):
        if self.cache:
            cached = self.cache.get(f"user:{user_id}")
            if cached:
                return cached
        
        user = f"User {user_id} from {self.database.connection_string}"
        if self.cache:
            self.cache.set(f"user:{user_id}", user)
        return user


class NotificationService:
    def __init__(self, email_service, user_repository):
        self.email_service = email_service
        self.user_repository = user_repository
    
    def notify_user(self, user_id, message):
        user = self.user_repository.get_user(user_id)
        return self.email_service.send_email(
            to=f"user{user_id}@example.com",
            subject="Notification",
            body=f"{user}: {message}"
        )


class Application:
    def __init__(self, notification_service, config):
        self.notification_service = notification_service
        self.config = config
        self.app_name = config.app.name()
        self.version = config.app.version()
    
    def run(self):
        print(f"Starting {self.app_name} v{self.version}")
        result = self.notification_service.notify_user(123, "Welcome to the app!")
        print(f"App result: {result}")
        return result


# Application Container
class ApplicationContainer(BaseContainer):
    # Configuration
    config = ConfigurationProvider("app_config")
    
    # Database
    database = SingletonProvider(
        DatabaseConnection,
        host=config.database.host,
        port=config.database.port.as_int(),
        database=config.database.name,
        username=config.database.username,
        password=config.database.password
    )
    
    # Cache (optional - only if enabled in config)
    cache = SingletonProvider(
        CacheService,
        host=config.cache.host,
        port=config.cache.port.as_int(),
        ttl=config.cache.ttl.as_int()
    )
    
    # Email service
    email_service = SingletonProvider(
        EmailService,
        smtp_host=config.email.smtp_host,
        smtp_port=config.email.smtp_port.as_int(),
        username=config.email.username,
        password=config.email.password,
        from_email=config.email.from_email
    )
    
    # Repository
    user_repository = SingletonProvider(
        UserRepository,
        database=database,
        cache=cache
    )
    
    # Services
    notification_service = SingletonProvider(
        NotificationService,
        email_service=email_service,
        user_repository=user_repository
    )
    
    # Application
    app = FactoryProvider(
        Application,
        notification_service=notification_service,
        config=config
    )


def test_production_setup():
    print("=== Production Setup ===")
    
    # Create container
    container = ApplicationContainer()
    
    # Load production configuration
    container.config.from_dict({
        "app": {
            "name": "Production App",
            "version": "2.1.0"
        },
        "database": {
            "host": "prod-db.example.com",
            "port": "5432",
            "name": "production_db",
            "username": "prod_user",
            "password": "secure_password"
        },
        "cache": {
            "host": "redis.example.com",
            "port": "6379",
            "ttl": "7200"
        },
        "email": {
            "smtp_host": "smtp.example.com",
            "smtp_port": "587",
            "username": "noreply@example.com",
            "password": "email_password",
            "from_email": "noreply@example.com"
        }
    })
    
    # Run application
    app = container.app()
    result = app.run()
    print(f"✓ Production result: {result}")


def test_development_setup():
    print("\n=== Development Setup ===")
    
    # Create container
    container = ApplicationContainer()
    
    # Load development configuration from JSON
    container.config.from_json("tests/examples/sample_config.json")
    
    # Override with development-specific settings
    container.config.from_dict({
        "database": {
            "username": "dev_user",
            "password": "dev_password"
        },
        "cache": {
            "host": "localhost",
            "port": "6379",
            "ttl": "300"
        },
        "email": {
            "smtp_host": "localhost",
            "smtp_port": "1025",
            "username": "dev@example.com",
            "password": "dev_password",
            "from_email": "dev@example.com"
        }
    })
    
    # Run application
    app = container.app()
    result = app.run()
    print(f"✓ Development result: {result}")


def test_testing_setup():
    print("\n=== Testing Setup ===")
    
    # Create container
    container = ApplicationContainer()
    
    # Load base configuration
    container.config.from_dict({
        "app": {
            "name": "Test App",
            "version": "1.0.0-test"
        },
        "database": {
            "host": "localhost",
            "port": "5432",
            "name": "test_db",
            "username": "test_user",
            "password": "test_password"
        },
        "cache": {
            "host": "localhost",
            "port": "6379",
            "ttl": "60"
        },
        "email": {
            "smtp_host": "localhost",
            "smtp_port": "1025",
            "username": "test@example.com",
            "password": "test_password",
            "from_email": "test@example.com"
        }
    })
    
    # Test with mocked services
    class MockEmailService:
        def __init__(self, *args, **kwargs):
            pass
        
        def send_email(self, to, subject, body):
            return f"MOCK: Email to {to} - {subject}"
    
    # Override email service for testing
    mock_email = SingletonProvider(MockEmailService)
    
    with container.override_providers(email_service=mock_email):
        app = container.app()
        result = app.run()
        print(f"✓ Testing result: {result}")


def test_environment_based_config():
    print("\n=== Environment-Based Configuration ===")
    
    # Set environment variables
    os.environ.update({
        'DB_HOST': 'env-db.example.com',
        'DB_PORT': '5432',
        'DB_NAME': 'env_database',
        'CACHE_ENABLED': 'true',
        'EMAIL_FROM': 'env@example.com'
    })
    
    try:
        container = ApplicationContainer()
        
        # Load configuration from environment
        container.config.from_dict({
            "app": {
                "name": "Environment App",
                "version": "1.0.0"
            },
            "database": {
                "host": container.config.from_env('DB_HOST'),
                "port": container.config.from_env('DB_PORT', as_=int),
                "name": container.config.from_env('DB_NAME'),
                "username": "env_user",
                "password": "env_password"
            },
            "cache": {
                "host": "localhost",
                "port": "6379",
                "ttl": "3600"
            },
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": "587",
                "username": "env_user",
                "password": "env_password",
                "from_email": container.config.from_env('EMAIL_FROM')
            }
        })
        
        app = container.app()
        result = app.run()
        print(f"✓ Environment result: {result}")
        
    finally:
        # Clean up environment
        for key in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'CACHE_ENABLED', 'EMAIL_FROM']:
            os.environ.pop(key, None)


if __name__ == "__main__":
    print("Real-World Configuration Example\n")
    
    test_production_setup()
    test_development_setup()
    test_testing_setup()
    test_environment_based_config()
    
    print("\n🎉 Real-world example completed!")