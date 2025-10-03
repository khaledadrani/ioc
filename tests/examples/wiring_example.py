"""Example demonstrating automatic dependency injection wiring."""

from inject import Container, FactoryProvider, SingletonProvider, Provide, inject


# Example services
class DatabaseConnection:
    def __init__(self, host="localhost", port=5432):
        self.host = host
        self.port = port
        print(f"Connected to database at {host}:{port}")
    
    def query(self, sql):
        return f"Result for: {sql}"


class CacheService:
    def __init__(self):
        self.data = {}
        print("Cache service initialized")
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value):
        self.data[key] = value


class UserRepository:
    def __init__(self, db, cache):
        self.db = db
        self.cache = cache
    
    def get_user(self, user_id):
        # Check cache first
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        
        # Query database
        result = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        self.cache.set(f"user:{user_id}", result)
        return result


# Business logic functions using automatic injection
@inject
def get_user_profile(user_id: int, db: DatabaseConnection = Provide('database')):
    """Get user profile with automatic database injection."""
    return db.query(f"SELECT profile FROM users WHERE id = {user_id}")


@inject
def update_user_cache(user_id: int, data: dict, 
                     cache: CacheService = Provide('cache')):
    """Update user cache with automatic cache injection."""
    cache.set(f"user:{user_id}", data)
    return f"Updated cache for user {user_id}"


@inject
def complex_operation(user_id: int,
                     db: DatabaseConnection = Provide('database'),
                     cache: CacheService = Provide('cache')):
    """Complex operation using multiple injected dependencies."""
    # Check cache
    cached = cache.get(f"complex:{user_id}")
    if cached:
        return cached
    
    # Perform complex database operations
    user_data = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    permissions = db.query(f"SELECT * FROM permissions WHERE user_id = {user_id}")
    
    result = {
        'user': user_data,
        'permissions': permissions,
        'computed': f"Complex result for {user_id}"
    }
    
    # Cache result
    cache.set(f"complex:{user_id}", result)
    return result


def main():
    """Demonstrate automatic dependency injection."""
    print("=== Automatic Dependency Injection Example ===\n")
    
    # Create container and configure providers
    container = Container()
    container.set_provider('database', FactoryProvider(
        lambda: DatabaseConnection("prod-db", 5432)
    ))
    container.set_provider('cache', SingletonProvider(CacheService))
    
    # Wire the container to enable automatic injection
    print("1. Wiring container for automatic injection...")
    container.wire()
    
    print("\n2. Calling functions with automatic injection:")
    
    # These functions will automatically receive their dependencies
    profile = get_user_profile(123)
    print(f"Profile: {profile}")
    
    update_result = update_user_cache(123, {"name": "John", "email": "john@example.com"})
    print(f"Cache update: {update_result}")
    
    complex_result = complex_operation(123)
    print(f"Complex operation: {complex_result}")
    
    print("\n3. Manual injection still works:")
    # You can still provide dependencies manually
    custom_db = DatabaseConnection("test-db", 3306)
    profile_with_custom_db = get_user_profile(456, db=custom_db)
    print(f"Profile with custom DB: {profile_with_custom_db}")
    
    print("\n4. Using injected dependencies in classes:")
    # Create repository with manual injection for demonstration
    repo = UserRepository(container.database(), container.cache())
    user_data = repo.get_user(789)
    print(f"Repository result: {user_data}")
    
    # Clean up
    container.unwire()
    print("\nContainer unwired.")


if __name__ == "__main__":
    main()