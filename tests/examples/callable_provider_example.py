#!/usr/bin/env python3
"""CallableProvider real-world examples demonstrating function-based dependency injection."""

from ioc import CallableProvider, FactoryProvider, SingletonProvider, Container
from ioc.wiring import inject, Provide


# Utility functions that will be used as providers
def calculate_tax(amount, rate=0.08):
    """Calculate tax for a given amount."""
    return round(amount * rate, 2)


def format_currency(amount, currency="USD", symbol="$"):
    """Format amount as currency."""
    return f"{symbol}{amount:.2f} {currency}"


def validate_email(email):
    """Simple email validation."""
    return "@" in email and "." in email.split("@")[1]


def generate_order_id(prefix="ORD"):
    """Generate a unique order ID."""
    import random
    return f"{prefix}_{random.randint(10000, 99999)}"


def calculate_shipping(weight, distance, rate_per_kg=2.5, rate_per_km=0.1):
    """Calculate shipping cost based on weight and distance."""
    return round((weight * rate_per_kg) + (distance * rate_per_km), 2)


def send_notification(message, channel="email", priority="normal"):
    """Send notification through specified channel."""
    return f"[{priority.upper()}] {channel}: {message}"


def audit_log(action, user_id, timestamp=None):
    """Create audit log entry."""
    if timestamp is None:
        from datetime import datetime
        timestamp = datetime.now().isoformat()
    return f"{timestamp} - User {user_id}: {action}"


# Business logic classes
class Product:
    def __init__(self, id, name, price, weight):
        self.id = id
        self.name = name
        self.price = price
        self.weight = weight


class Order:
    def __init__(self, id, user_id, products, shipping_distance=10):
        self.id = id
        self.user_id = user_id
        self.products = products
        self.shipping_distance = shipping_distance
        self.subtotal = sum(p.price for p in products)
        self.total_weight = sum(p.weight for p in products)


class OrderProcessor:
    def __init__(self, tax_calc, currency_fmt, shipping_calc, order_id_gen, notifier, auditor):
        self.tax_calc = tax_calc
        self.currency_fmt = currency_fmt
        self.shipping_calc = shipping_calc
        self.order_id_gen = order_id_gen
        self.notifier = notifier
        self.auditor = auditor
    
    def process_order(self, user_id, products, shipping_distance=10):
        # Generate order ID
        order_id = self.order_id_gen()
        
        # Create order
        order = Order(order_id, user_id, products, shipping_distance)
        
        # Calculate costs
        tax = self.tax_calc(order.subtotal)
        shipping = self.shipping_calc(order.total_weight, order.shipping_distance)
        total = order.subtotal + tax + shipping
        
        # Format for display
        subtotal_str = self.currency_fmt(order.subtotal)
        tax_str = self.currency_fmt(tax)
        shipping_str = self.currency_fmt(shipping)
        total_str = self.currency_fmt(total)
        
        # Log the action
        audit_entry = self.auditor("ORDER_PROCESSED", user_id)
        
        # Send notification
        notification = self.notifier(
            f"Order {order_id} processed. Total: {total_str}",
            channel="email",
            priority="high"
        )
        
        return {
            "order_id": order_id,
            "subtotal": subtotal_str,
            "tax": tax_str,
            "shipping": shipping_str,
            "total": total_str,
            "audit": audit_entry,
            "notification": notification
        }


class UserService:
    def __init__(self, email_validator, notifier, auditor):
        self.email_validator = email_validator
        self.notifier = notifier
        self.auditor = auditor
    
    def register_user(self, email, name):
        # Validate email
        if not self.email_validator(email):
            raise ValueError(f"Invalid email: {email}")
        
        # Simulate user creation
        user_id = f"user_{hash(email) % 10000}"
        
        # Log registration
        audit_entry = self.auditor("USER_REGISTERED", user_id)
        
        # Send welcome notification
        notification = self.notifier(
            f"Welcome {name}! Your account has been created.",
            channel="email",
            priority="normal"
        )
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "audit": audit_entry,
            "notification": notification
        }


# Container configuration
class ECommerceContainer(Container):
    # Callable providers for utility functions
    tax_calculator = CallableProvider(calculate_tax, rate=0.085)  # 8.5% tax
    currency_formatter = CallableProvider(format_currency, currency="USD", symbol="$")
    email_validator = CallableProvider(validate_email)
    order_id_generator = CallableProvider(generate_order_id, prefix="ORDER")
    shipping_calculator = CallableProvider(calculate_shipping, rate_per_kg=3.0, rate_per_km=0.15)
    notification_sender = CallableProvider(send_notification, channel="email")
    audit_logger = CallableProvider(audit_log)
    
    # Service providers
    order_processor = FactoryProvider(
        OrderProcessor,
        tax_calc=tax_calculator,
        currency_fmt=currency_formatter,
        shipping_calc=shipping_calculator,
        order_id_gen=order_id_generator,
        notifier=notification_sender,
        auditor=audit_logger
    )
    
    user_service = FactoryProvider(
        UserService,
        email_validator=email_validator,
        notifier=notification_sender,
        auditor=audit_logger
    )


def test_callable_provider_basic_usage():
    """Test basic CallableProvider functionality."""
    print("=== Basic CallableProvider Usage ===")
    
    # Create individual callable providers
    tax_calc = CallableProvider(calculate_tax, rate=0.1)  # 10% tax
    currency_fmt = CallableProvider(format_currency, currency="EUR", symbol="€")
    
    # Use the providers
    tax_amount = tax_calc(100)  # 100 * 0.1 = 10
    formatted = currency_fmt(110)  # €110.00 EUR
    
    print(f"✓ Tax calculation: {tax_amount}")
    print(f"✓ Currency formatting: {formatted}")


def test_callable_provider_with_dependencies():
    """Test CallableProvider with other provider dependencies."""
    print("\n=== CallableProvider with Dependencies ===")
    
    # Create a provider that depends on another provider
    class TaxRateProvider:
        def __init__(self, base_rate):
            self.base_rate = base_rate
        
        def get_rate(self):
            return self.base_rate
    
    rate_provider = FactoryProvider(TaxRateProvider, base_rate=0.075)
    
    # This won't work directly because CallableProvider expects the dependency to return the value
    # Instead, we need to create a wrapper
    def get_tax_rate():
        return rate_provider().get_rate()
    
    rate_callable = CallableProvider(get_tax_rate)
    
    def calculate_tax_with_provider(amount, rate_provider):
        rate = rate_provider()
        return amount * rate
    
    tax_calc = CallableProvider(calculate_tax_with_provider, rate_provider=rate_callable)
    
    result = tax_calc(200)
    print(f"✓ Tax with provider dependency: {result}")


def test_ecommerce_example():
    """Test complete e-commerce example with CallableProvider."""
    print("\n=== E-Commerce Example ===")
    
    container = ECommerceContainer()
    
    # Create some sample products
    products = [
        Product("P001", "Laptop", 999.99, 2.5),
        Product("P002", "Mouse", 29.99, 0.2),
        Product("P003", "Keyboard", 79.99, 0.8)
    ]
    
    # Process an order
    order_processor = container.order_processor()
    result = order_processor.process_order("user123", products, shipping_distance=50)
    
    print("Order Processing Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Register a user
    user_service = container.user_service()
    user_result = user_service.register_user("john@example.com", "John Doe")
    
    print("\nUser Registration Result:")
    for key, value in user_result.items():
        print(f"  {key}: {value}")


def test_callable_provider_overriding():
    """Test CallableProvider overriding for different environments."""
    print("\n=== CallableProvider Overriding ===")
    
    container = ECommerceContainer()
    
    # Original tax calculation (8.5%)
    order_processor = container.order_processor()
    products = [Product("P001", "Item", 100.0, 1.0)]
    
    result1 = order_processor.process_order("user1", products)
    print(f"✓ Original tax: {result1['tax']}")
    
    # Override with different tax rate for testing
    test_tax_calc = CallableProvider(calculate_tax, rate=0.0)  # 0% tax for testing
    
    with container.tax_calculator.override(test_tax_calc):
        order_processor = container.order_processor()
        result2 = order_processor.process_order("user1", products)
        print(f"✓ Test tax (0%): {result2['tax']}")
    
    # Back to original
    result3 = order_processor.process_order("user1", products)
    print(f"✓ Back to original tax: {result3['tax']}")


def test_wiring_with_callable_providers():
    """Test automatic wiring with CallableProvider."""
    print("\n=== Wiring with CallableProvider ===")
    
    container = ECommerceContainer()
    container.wire(modules=[__name__])
    
    # Functions that use callable providers through wiring
    @inject
    def calculate_order_total(subtotal: float, 
                            tax_calc=Provide('tax_calculator'),
                            currency_fmt=Provide('currency_formatter')):
        tax = tax_calc(subtotal)
        total = subtotal + tax
        return currency_fmt(total)
    
    @inject
    def validate_and_format_email(email: str,
                                validator=Provide('email_validator')):
        if validator(email):
            return f"✓ Valid email: {email}"
        else:
            return f"✗ Invalid email: {email}"
    
    @inject
    def create_audit_entry(action: str, user_id: str,
                          auditor=Provide('audit_logger')):
        return auditor(action, user_id)
    
    # Test the wired functions
    total = calculate_order_total(100.0)
    print(f"✓ Order total: {total}")
    
    email_check1 = validate_and_format_email("valid@example.com")
    email_check2 = validate_and_format_email("invalid-email")
    print(f"✓ Email validation 1: {email_check1}")
    print(f"✓ Email validation 2: {email_check2}")
    
    audit = create_audit_entry("LOGIN", "user456")
    print(f"✓ Audit entry: {audit}")
    
    container.unwire()


def test_callable_provider_performance():
    """Test CallableProvider performance characteristics."""
    print("\n=== CallableProvider Performance ===")
    
    import time
    
    # Create providers
    simple_calc = CallableProvider(calculate_tax, rate=0.1)
    
    # Test multiple calls
    start_time = time.time()
    results = []
    for i in range(1000):
        result = simple_calc(i)
        results.append(result)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✓ 1000 calls completed in {duration:.4f} seconds")
    print(f"✓ Average per call: {duration/1000*1000:.4f} ms")
    print(f"✓ Sample results: {results[:5]}")


if __name__ == "__main__":
    print("CallableProvider Real-World Examples\n")
    
    test_callable_provider_basic_usage()
    test_callable_provider_with_dependencies()
    test_ecommerce_example()
    test_callable_provider_overriding()
    test_wiring_with_callable_providers()
    test_callable_provider_performance()
    
    print("\n🎉 CallableProvider examples completed!")