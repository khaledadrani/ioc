# Unit Test Style Guide

This document describes the unit testing patterns and conventions used in this project, based on the implementation in `tests/unit_tests/test_blob_storage.py`.

## Test Structure Pattern

### Class-Based Test Organization
```python
class TestBlobStorageService:
    def setup_method(self):
        # Initialize common test data and mocks
        
    def test_method_name_scenario(self):
        # Test implementation
```

### Setup Method Pattern
```python
def setup_method(self):
    # 1. Define test configuration
    self.endpoint = "localhost:9000"
    self.access_key = "minioadmin"
    self.secret_key = "minioadmin"
    self.secure = False
    self.bucket_name = "default-bucket"

    # 2. Create mock objects
    self.client_mock = MagicMock(MinioClientProtocol)

    # 3. Initialize service under test with mocks
    self.service = BlobStorageService(
        endpoint=self.endpoint,
        access_key=self.access_key,
        secret_key=self.secret_key,
        secure=self.secure,
        bucket_name=self.bucket_name,
        client=self.client_mock
    )
```

## Test Method Patterns

### 1. Success Case Pattern
```python
def test_upload_file_success(self):
    # Arrange: Setup mocks and test data
    service = self.service
    client_mock = self.client_mock
    client_mock.bucket_exists.return_value = False
    client_mock.make_bucket.return_value = None
    client_mock.fput_object.return_value = None

    file_path = "test.txt"
    object_name = "test-object.txt"
    
    # Act: Execute the method under test
    with patch("os.path.exists", return_value=True):
        result = service.upload_file(file_path=file_path, object_name=object_name)

    # Assert: Verify results and mock calls
    assert result == object_name
    client_mock.fput_object.assert_called_once_with(
        self.bucket_name,
        object_name,
        file_path,
        metadata={"uploaded_at": client_mock.fput_object.call_args[1]["metadata"]["uploaded_at"]}
    )
```

### 2. Exception Handling Pattern
```python
def test_upload_file_not_found(self):
    # Mock external dependencies to trigger exception
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            self.service.upload_file(file_path="non_existent_file.txt", 
                                object_name="test-object.txt")
    
    # Verify no side effects occurred
    self.client_mock.fput_object.assert_not_called()
```

### 3. S3Error Exception Pattern
```python
def test_upload_file_exception_failure(self):
    # Arrange: Setup mock to raise S3Error
    client_mock = self.client_mock
    client_mock.bucket_exists.return_value = True
    client_mock.fput_object.side_effect = S3Error(
        code="AccessDenied",
        message="Access denied",
        resource="test-object.txt",
        request_id="12345",
        host_id="abcde",
        response="Access denied"
    )

    # Act & Assert: Verify custom exception is raised
    with patch("os.path.exists", return_value=True):
        with pytest.raises(UploadFailedException) as exc_info:
            service.upload_file(file_path=file_path, object_name=object_name)

    # Verify exception message and mock calls
    assert "Access denied" in str(exc_info.value)
    client_mock.fput_object.assert_called_once()
```

## Key Testing Principles

### 1. Mock External Dependencies
- Always mock the MinIO client using `MagicMock(MinioClientProtocol)`
- Mock file system operations with `patch("os.path.exists")`
- Mock any external API calls or I/O operations

### 2. Test Naming Convention
```python
def test_{method_name}_{scenario}(self):
    # Examples:
    # test_upload_file_success
    # test_upload_file_not_found
    # test_upload_file_exception_failure
    # test_search_by_name_success
```

### 3. Arrange-Act-Assert Pattern
```python
def test_method_scenario(self):
    # Arrange: Setup test data and mocks
    service = self.service
    client_mock = self.client_mock
    # ... setup mocks and data
    
    # Act: Execute the method under test
    result = service.method_under_test(parameters)
    
    # Assert: Verify results and side effects
    assert result == expected_value
    client_mock.method.assert_called_once_with(expected_args)
```

### 4. Mock Response Objects
```python
def test_download_data_success(self):
    # Create mock response with required methods
    mock_response = MagicMock()
    mock_response.read.return_value = expected_data
    client_mock.get_object.return_value = mock_response

    result = service.download_data(object_name=object_name)

    # Verify all response methods were called
    mock_response.close.assert_called_once()
    mock_response.release_conn.assert_called_once()
```

## Common Mock Patterns

### 1. Mock Return Values
```python
client_mock.bucket_exists.return_value = True
client_mock.list_objects.return_value = mock_objects
```

### 2. Mock Side Effects (Exceptions)
```python
client_mock.fput_object.side_effect = S3Error(...)
```

### 3. Mock Complex Objects
```python
mock_objects = [
    MagicMock(object_name="test-object.txt"),
    MagicMock(object_name="another-object.txt")
]
```

### 4. Context Manager Patching
```python
with patch("os.path.exists", return_value=True):
    result = service.method()
```

## Assertion Patterns

### 1. Result Verification
```python
assert result == expected_value
assert len(result) == expected_count
assert result[0]["name"] == "expected_name"
```

### 2. Mock Call Verification
```python
# Verify method was called once with specific args
client_mock.method.assert_called_once_with(arg1, arg2)

# Verify method was not called
client_mock.method.assert_not_called()

# Verify call count
assert client_mock.method.call_count == 2
```

### 3. Exception Message Verification
```python
with pytest.raises(CustomException) as exc_info:
    service.method()

assert "expected message" in str(exc_info.value)
```

### 4. Dynamic Argument Verification
```python
# When exact values can't be predicted (like timestamps)
args, kwargs = client_mock.method.call_args
assert args[0] == expected_bucket
assert "uploaded_at" in kwargs["metadata"]
```

## Skip Pattern
```python
@pytest.mark.skip(reason="Skipping, no need to test this for now")
def test_method_scenario(self):
    # Test implementation
```

## Best Practices

1. **One assertion per logical concept** - Don't over-assert
2. **Mock at the boundary** - Mock external dependencies, not internal logic
3. **Test behavior, not implementation** - Focus on what the method should do
4. **Use descriptive test names** - Make failures easy to understand
5. **Keep tests independent** - Each test should be able to run in isolation
6. **Verify both success and failure paths** - Test happy path and edge cases

This style provides comprehensive coverage while maintaining readability and maintainability.