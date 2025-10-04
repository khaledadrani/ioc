#!/usr/bin/env python3
"""Real-world example using Configuration provider with a complete application setup."""

import os
from ioc.config_provider import ConfigurationProvider
from ioc.providers import FactoryProvider, SingletonProvider
from ioc.container import BaseContainer
from ioc.wiring import inject, Provide


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
        # Access config values properly - config is the ConfigurationProvider instance
        self.app_name = config.get('app.name')
        self.version = config.get('app.version')
    
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


def test_automatic_wiring():
    print("\n=== Automatic Wiring Examples ===")
    
    # Create container
    container = ApplicationContainer()
    container.config.from_dict({
        "app": {"name": "Wired App", "version": "1.0.0"},
        "database": {"host": "localhost", "port": "5432", "name": "wired_db", "username": "user", "password": "pass"},
        "cache": {"host": "localhost", "port": "6379", "ttl": "3600"},
        "email": {"smtp_host": "localhost", "smtp_port": "587", "username": "test", "password": "test", "from_email": "test@example.com"}
    })
    
    # Wire the container to this module
    container.wire(modules=[__name__])
    
    # Example 1: Function with automatic injection
    @inject
    def get_user_info(user_id: int, repo: UserRepository = Provide('user_repository')):
        return repo.get_user(user_id)
    
    # Example 2: Function with multiple injections
    @inject
    def send_notification(user_id: int, message: str, 
                         service: NotificationService = Provide('notification_service')):
        return service.notify_user(user_id, message)
    
    # Example 3: Function with config injection
    @inject
    def get_app_info(config: ConfigurationProvider = Provide('config')):
        return f"App: {config.get('app.name')} v{config.get('app.version')}"
    
    # Example 4: Business logic function
    @inject
    def process_user_registration(user_id: int, email: str,
                                 db: DatabaseConnection = Provide('database'),
                                 cache: CacheService = Provide('cache'),
                                 email_service: EmailService = Provide('email_service')):
        # Simulate user registration process
        db_result = db.connect()
        cache_result = cache.set(f"user:{user_id}", email)
        email_result = email_service.send_email(email, "Welcome!", "Thanks for registering")
        return f"Registration: {db_result}, {cache_result}, {email_result}"
    
    # Test the wired functions
    print("\n--- Testing Wired Functions ---")
    
    # These functions will automatically receive their dependencies
    user_info = get_user_info(123)
    print(f"✓ User info: {user_info}")
    
    notification = send_notification(123, "Welcome!")
    print(f"✓ Notification: {notification}")
    
    app_info = get_app_info()
    print(f"✓ App info: {app_info}")
    
    registration = process_user_registration(456, "user@example.com")
    print(f"✓ Registration: {registration}")
    
    # Example 5: Manual override of injected parameters
    @inject
    def flexible_function(message: str, 
                         service: NotificationService = Provide('notification_service')):
        return service.notify_user(999, message)
    
    # Can still provide parameters manually
    manual_service = container.notification_service()
    manual_result = flexible_function("Manual message", service=manual_service)
    print(f"✓ Manual override: {manual_result}")
    
    # Clean up wiring
    container.unwire()
    print("✓ Container unwired")


def test_wiring_with_classes():
    print("\n=== Wiring with Classes ===")
    
    container = ApplicationContainer()
    container.config.from_dict({
        "app": {"name": "Class Wired App", "version": "2.0.0"},
        "database": {"host": "localhost", "port": "5432", "name": "class_db", "username": "user", "password": "pass"},
        "cache": {"host": "localhost", "port": "6379", "ttl": "1800"},
        "email": {"smtp_host": "localhost", "smtp_port": "587", "username": "class", "password": "test", "from_email": "class@example.com"}
    })
    
    container.wire(modules=[__name__])
    
    # Example: Service class with injected methods
    class UserService:
        @inject
        def create_user(self, user_data: dict, 
                       db: DatabaseConnection = Provide('database'),
                       cache: CacheService = Provide('cache')):
            db_result = db.connect()
            cache_result = cache.set(f"user:{user_data['id']}", str(user_data))
            return f"User created: {db_result}, {cache_result}"
        
        @inject
        def send_welcome_email(self, user_id: int,
                              email_service: EmailService = Provide('email_service')):
            return email_service.send_email(
                f"user{user_id}@example.com", 
                "Welcome!", 
                "Welcome to our service!"
            )
    
    # Test class methods with injection
    user_service = UserService()
    
    create_result = user_service.create_user({"id": 789, "name": "John Doe"})
    print(f"✓ Create user: {create_result}")
    
    email_result = user_service.send_welcome_email(789)
    print(f"✓ Welcome email: {email_result}")
    
    container.unwire()
    print("✓ Class wiring test completed")


def test_wiring_patterns():
    print("\n=== Advanced Wiring Patterns ===")
    
    container = ApplicationContainer()
    container.config.from_dict({
        "app": {"name": "Pattern App", "version": "3.0.0"},
        "database": {"host": "localhost", "port": "5432", "name": "pattern_db", "username": "user", "password": "pass"},
        "cache": {"host": "localhost", "port": "6379", "ttl": "900"},
        "email": {"smtp_host": "localhost", "smtp_port": "587", "username": "pattern", "password": "test", "from_email": "pattern@example.com"}
    })
    
    container.wire(modules=[__name__])
    
    # Pattern 1: Repository pattern with injection
    @inject
    def get_user_by_email(email: str, 
                         repo: UserRepository = Provide('user_repository')):
        # Simulate finding user by email
        return f"Found user with email {email}: {repo.get_user(hash(email) % 1000)}"
    
    # Pattern 2: Service layer with multiple dependencies
    @inject
    def process_order(order_id: int, user_id: int,
                     db: DatabaseConnection = Provide('database'),
                     cache: CacheService = Provide('cache'),
                     notification: NotificationService = Provide('notification_service')):
        # Simulate order processing
        db_save = f"Order {order_id} saved to {db.connection_string}"
        cache_update = cache.set(f"order:{order_id}", f"user:{user_id}")
        notify_result = notification.notify_user(user_id, f"Order {order_id} processed")
        return f"Order processed: {db_save}, {cache_update}, {notify_result}"
    
    # Pattern 3: Factory function with injection
    @inject
    def create_user_session(user_id: int,
                           cache: CacheService = Provide('cache'),
                           config: ConfigurationProvider = Provide('config')):
        session_id = f"session_{user_id}_{hash(user_id) % 10000}"
        app_name = config.get('app.name')
        cache.set(f"session:{session_id}", f"user:{user_id}")
        return f"Session created for {app_name}: {session_id}"
    
    # Test the patterns
    print("\n--- Testing Wiring Patterns ---")
    
    user_result = get_user_by_email("john@example.com")
    print(f"✓ User lookup: {user_result}")
    
    order_result = process_order(12345, 789)
    print(f"✓ Order processing: {order_result}")
    
    session_result = create_user_session(789)
    print(f"✓ Session creation: {session_result}")
    
    container.unwire()
    print("✓ Advanced patterns test completed")


if __name__ == "__main__":
    print("Real-World Configuration Example\n")
    
    test_production_setup()
    test_development_setup()
    test_testing_setup()
    test_environment_based_config()
    test_automatic_wiring()
    test_wiring_with_classes()
    test_wiring_patterns()
    
    print("\n🎉 Real-world example completed!")