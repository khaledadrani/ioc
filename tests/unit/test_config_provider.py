import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open

from ioc.config_provider import ConfigurationProvider, ConfigurationOption, TypedConfigurationOption
from ioc.base_provider import Provider
from ioc.exceptions import ProvideObjectError


class TestConfigurationProvider:
    def setup_method(self):
        self.config = ConfigurationProvider("test_config")

    def test_configuration_provider_inherits_from_provider(self):
        # Assert
        assert isinstance(self.config, Provider)

    def test_configuration_provider_initialization_success(self):
        # Assert
        assert self.config._name == "test_config"
        assert self.config._data == {}
        assert isinstance(self.config._children, dict)

    def test_configuration_provider_initialization_with_default(self):
        # Arrange
        default_data = {"key": "value"}
        config = ConfigurationProvider("test", default=default_data)
        
        # Assert
        assert config._data == default_data

    def test_configuration_provider_call_returns_data(self):
        # Arrange
        test_data = {"app": {"name": "test"}}
        self.config.from_dict(test_data)
        
        # Act
        result = self.config()
        
        # Assert
        assert result == test_data

    def test_from_dict_success(self):
        # Arrange
        test_data = {"database": {"host": "localhost", "port": 5432}}
        
        # Act
        result = self.config.from_dict(test_data)
        
        # Assert
        assert result == self.config  # Returns self for chaining
        assert self.config._data == test_data

    def test_from_dict_invalid_type_raises_error(self):
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            self.config.from_dict("not_a_dict")
        
        assert "Configuration data must be a dictionary" in str(exc_info.value)

    def test_from_json_success(self):
        # Arrange
        test_data = {"app": {"name": "test_app"}}
        json_content = json.dumps(test_data)
        
        with patch("builtins.open", mock_open(read_data=json_content)):
            # Act
            result = self.config.from_json("test.json")
        
        # Assert
        assert result == self.config
        assert self.config._data == test_data

    def test_from_json_file_not_found_raises_error(self):
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            self.config.from_json("nonexistent.json")
        
        assert "Failed to load JSON config" in str(exc_info.value)

    def test_from_json_invalid_json_raises_error(self):
        # Arrange
        invalid_json = "{'invalid': json}"
        
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            # Act & Assert
            with pytest.raises(ProvideObjectError) as exc_info:
                self.config.from_json("invalid.json")
        
        assert "Failed to load JSON config" in str(exc_info.value)

    def test_from_yaml_success(self):
        # Arrange
        yaml_content = "app:\n  name: test_app\n  version: 1.0"
        expected_data = {"app": {"name": "test_app", "version": 1.0}}
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("ioc.config_provider.yaml") as mock_yaml:
                mock_yaml.safe_load.return_value = expected_data
                
                # Act
                result = self.config.from_yaml("test.yaml")
        
        # Assert
        assert result == self.config
        assert self.config._data == expected_data

    def test_from_yaml_no_yaml_module_raises_error(self):
        # Arrange
        with patch("ioc.config_provider.yaml", None):
            # Act & Assert
            with pytest.raises(ProvideObjectError) as exc_info:
                self.config.from_yaml("test.yaml")
        
        assert "PyYAML not installed" in str(exc_info.value)

    def test_from_yaml_file_not_found_raises_error(self):
        # Arrange
        with patch("ioc.config_provider.yaml") as mock_yaml:
            # Act & Assert
            with pytest.raises(ProvideObjectError) as exc_info:
                self.config.from_yaml("nonexistent.yaml")
        
        assert "Failed to load YAML config" in str(exc_info.value)

    def test_from_env_success(self):
        # Arrange
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            # Act
            result = self.config.from_env("TEST_VAR")
        
        # Assert
        assert result == "test_value"

    def test_from_env_with_default_success(self):
        # Act
        result = self.config.from_env("NONEXISTENT_VAR", default="default_value")
        
        # Assert
        assert result == "default_value"

    def test_from_env_missing_var_raises_error(self):
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            self.config.from_env("NONEXISTENT_VAR")
        
        assert "Environment variable 'NONEXISTENT_VAR' not found" in str(exc_info.value)

    def test_from_env_with_type_conversion_success(self):
        # Arrange
        with patch.dict(os.environ, {"TEST_PORT": "8080"}):
            # Act
            result = self.config.from_env("TEST_PORT", as_=int)
        
        # Assert
        assert result == 8080
        assert isinstance(result, int)

    def test_from_env_type_conversion_error_raises_error(self):
        # Arrange
        with patch.dict(os.environ, {"TEST_VAR": "not_a_number"}):
            # Act & Assert
            with pytest.raises(ProvideObjectError) as exc_info:
                self.config.from_env("TEST_VAR", as_=int)
        
        assert "Failed to convert env var 'TEST_VAR'" in str(exc_info.value)

    def test_get_success(self):
        # Arrange
        self.config.from_dict({
            "database": {
                "host": "localhost",
                "port": 5432
            }
        })
        
        # Act
        host = self.config.get("database.host")
        port = self.config.get("database.port")
        
        # Assert
        assert host == "localhost"
        assert port == 5432

    def test_get_with_default_success(self):
        # Act
        result = self.config.get("nonexistent.key", default="default_value")
        
        # Assert
        assert result == "default_value"

    def test_get_missing_key_returns_default(self):
        # Arrange
        self.config.from_dict({"key": "value"})
        
        # Act
        result = self.config.get("missing.key")
        
        # Assert
        assert result is None

    def test_set_success(self):
        # Act
        result = self.config.set("database.host", "localhost")
        
        # Assert
        assert result == self.config
        assert self.config.get("database.host") == "localhost"

    def test_set_nested_key_success(self):
        # Act
        self.config.set("app.database.host", "localhost")
        
        # Assert
        assert self.config.get("app.database.host") == "localhost"

    def test_getattr_creates_configuration_option(self):
        # Act
        option = self.config.database
        
        # Assert
        assert isinstance(option, ConfigurationOption)
        assert option._name == "database"
        assert option._root == self.config

    def test_getattr_private_attribute_raises_error(self):
        # Act & Assert
        with pytest.raises(AttributeError):
            _ = self.config._private_attr

    def test_getitem_creates_configuration_option(self):
        # Act
        option = self.config["database"]
        
        # Assert
        assert isinstance(option, ConfigurationOption)
        assert option._name == "database"

    def test_configuration_option_caching(self):
        # Act
        option1 = self.config.database
        option2 = self.config.database
        
        # Assert
        assert option1 is option2


class TestConfigurationOption:
    def setup_method(self):
        self.root_config = ConfigurationProvider("test")
        self.root_config.from_dict({
            "database": {
                "host": "localhost",
                "port": 5432,
                "nested": {
                    "value": "deep"
                }
            }
        })
        self.option = ConfigurationOption("database", self.root_config)

    def test_configuration_option_initialization_success(self):
        # Assert
        assert self.option._name == "database"
        assert self.option._root == self.root_config
        assert isinstance(self.option._children, dict)

    def test_configuration_option_call_returns_value(self):
        # Act
        result = self.option()
        
        # Assert
        expected = {"host": "localhost", "port": 5432, "nested": {"value": "deep"}}
        assert result == expected

    def test_configuration_option_nested_access(self):
        # Act
        host_option = self.option.host
        
        # Assert
        assert isinstance(host_option, ConfigurationOption)
        assert host_option._name == "database.host"
        assert host_option() == "localhost"

    def test_configuration_option_deep_nesting(self):
        # Act
        deep_option = self.option.nested.value
        
        # Assert
        assert isinstance(deep_option, ConfigurationOption)
        assert deep_option._name == "database.nested.value"
        assert deep_option() == "deep"

    def test_configuration_option_getitem_access(self):
        # Act
        host_option = self.option["host"]
        
        # Assert
        assert isinstance(host_option, ConfigurationOption)
        assert host_option() == "localhost"

    def test_configuration_option_private_attribute_raises_error(self):
        # Act & Assert
        with pytest.raises(AttributeError):
            _ = self.option._private

    def test_configuration_option_as_int_success(self):
        # Act
        port_typed = self.option.port.as_int()
        
        # Assert
        assert isinstance(port_typed, TypedConfigurationOption)
        assert port_typed() == 5432
        assert isinstance(port_typed(), int)

    def test_configuration_option_as_float_success(self):
        # Arrange
        self.root_config.set("database.timeout", "30.5")
        
        # Act
        timeout_typed = self.option.timeout.as_float()
        
        # Assert
        assert isinstance(timeout_typed, TypedConfigurationOption)
        assert timeout_typed() == 30.5
        assert isinstance(timeout_typed(), float)

    def test_configuration_option_as_bool_success(self):
        # Arrange
        self.root_config.set("database.ssl", "true")
        
        # Act
        ssl_typed = self.option.ssl.as_bool()
        
        # Assert
        assert isinstance(ssl_typed, TypedConfigurationOption)
        assert ssl_typed() is True
        assert isinstance(ssl_typed(), bool)

    def test_configuration_option_child_caching(self):
        # Act
        host1 = self.option.host
        host2 = self.option.host
        
        # Assert
        assert host1 is host2


class TestTypedConfigurationOption:
    def setup_method(self):
        self.root_config = ConfigurationProvider("test")
        self.root_config.from_dict({
            "values": {
                "port": "8080",
                "timeout": "30.5",
                "debug": "true",
                "count": "42"
            }
        })

    def test_typed_configuration_option_initialization_success(self):
        # Arrange
        option = self.root_config.values.port
        
        # Act
        typed_option = TypedConfigurationOption(int, option)
        
        # Assert
        assert typed_option._converter == int
        assert typed_option._option == option

    def test_int_conversion_success(self):
        # Act
        result = self.root_config.values.port.as_int()()
        
        # Assert
        assert result == 8080
        assert isinstance(result, int)

    def test_float_conversion_success(self):
        # Act
        result = self.root_config.values.timeout.as_float()()
        
        # Assert
        assert result == 30.5
        assert isinstance(result, float)

    def test_bool_conversion_true_success(self):
        # Act
        result = self.root_config.values.debug.as_bool()()
        
        # Assert
        assert result is True
        assert isinstance(result, bool)

    def test_bool_conversion_false_success(self):
        # Arrange
        self.root_config.set("values.debug", "false")
        
        # Act
        result = self.root_config.values.debug.as_bool()()
        
        # Assert
        assert result is False

    def test_bool_conversion_various_true_values(self):
        # Arrange & Act & Assert
        for true_value in ["true", "1", "yes", "on", "TRUE", "True"]:
            self.root_config.set("values.test_bool", true_value)
            result = self.root_config.values.test_bool.as_bool()()
            assert result is True, f"Failed for value: {true_value}"

    def test_bool_conversion_various_false_values(self):
        # Arrange & Act & Assert
        for false_value in ["false", "0", "no", "off", "FALSE", "False", ""]:
            self.root_config.set("values.test_bool", false_value)
            result = self.root_config.values.test_bool.as_bool()()
            assert result is False, f"Failed for value: {false_value}"

    def test_conversion_with_none_value_returns_none(self):
        # Arrange
        option = ConfigurationOption("nonexistent", self.root_config)
        typed_option = TypedConfigurationOption(int, option)
        
        # Act
        result = typed_option()
        
        # Assert
        assert result is None

    def test_conversion_error_raises_provide_object_error(self):
        # Arrange
        self.root_config.set("values.invalid", "not_a_number")
        
        # Act & Assert
        with pytest.raises(ProvideObjectError) as exc_info:
            self.root_config.values.invalid.as_int()()
        
        assert "Failed to convert config value" in str(exc_info.value)

    def test_custom_converter_success(self):
        # Arrange
        def custom_converter(value):
            return f"custom_{value}"
        
        option = self.root_config.values.port
        typed_option = TypedConfigurationOption(custom_converter, option)
        
        # Act
        result = typed_option()
        
        # Assert
        assert result == "custom_8080"


class TestConfigurationProviderIntegration:
    def test_real_json_file_loading(self):
        # Arrange
        test_data = {
            "app": {"name": "TestApp", "version": "1.0.0"},
            "database": {"host": "localhost", "port": 5432}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name
        
        try:
            config = ConfigurationProvider()
            
            # Act
            config.from_json(json_file)
            
            # Assert
            assert config.app.name() == "TestApp"
            assert config.database.port.as_int()() == 5432
        finally:
            os.unlink(json_file)

    def test_configuration_chaining(self):
        # Arrange
        config = ConfigurationProvider()
        
        # Act
        result = config.from_dict({"key1": "value1"}).set("key2", "value2")
        
        # Assert
        assert result == config
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"

    def test_configuration_override_behavior(self):
        # Arrange
        config = ConfigurationProvider()
        config.from_dict({"database": {"host": "original", "port": 5432}})
        
        # Act
        config.from_dict({"database": {"host": "updated"}})
        
        # Assert
        assert config.database.host() == "updated"
        assert config.database.port() == 5432  # Should be preserved

    def test_complex_nested_configuration(self):
        # Arrange
        config = ConfigurationProvider()
        complex_data = {
            "app": {
                "name": "ComplexApp",
                "features": {
                    "auth": {"enabled": True, "provider": "oauth"},
                    "cache": {"enabled": False, "ttl": 3600}
                }
            }
        }
        
        # Act
        config.from_dict(complex_data)
        
        # Assert
        assert config.app.name() == "ComplexApp"
        assert config.app.features.auth.enabled.as_bool()() is True
        assert config.app.features.auth.provider() == "oauth"
        assert config.app.features.cache.enabled.as_bool()() is False
        assert config.app.features.cache.ttl.as_int()() == 3600