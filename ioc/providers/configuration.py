"""Configuration provider for loading settings from various sources."""

import json
import os
from ..exceptions import ProvideObjectError, ConfigurationNotLoadedError
from .base import Provider

try:
    import yaml
except ImportError:
    yaml = None


class ConfigurationProvider(Provider):
    """Configuration provider for loading settings from files and environment."""
    
    def __init__(self, name="config", default=None):
        super().__init__()
        self._name = name
        self._data = default or {}
        self._children = {}
    
    def __getattr__(self, name):
        """Get configuration option by attribute access."""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        if name not in self._children:
            self._children[name] = ConfigurationOption(name, self)
        return self._children[name]
    
    def __getitem__(self, key):
        """Get configuration option by key access."""
        return self.__getattr__(key)
    
    def _provide(self, args, kwargs):
        """Return the configuration data."""
        return self._data
    
    def from_dict(self, data):
        """Load configuration from dictionary."""
        if not isinstance(data, dict):
            raise ProvideObjectError("Configuration data must be a dictionary")
        self._deep_merge(self._data, data)
        return self
    
    def _deep_merge(self, target, source):
        """Deep merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def from_json(self, filepath):
        """Load configuration from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ProvideObjectError(f"Failed to load JSON config: {e}")
        return self
    
    def from_yaml(self, filepath):
        """Load configuration from YAML file."""
        if yaml is None:
            raise ProvideObjectError("PyYAML not installed. Install with: pip install pyyaml")
        
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            self.from_dict(data)
        except Exception as e:
            raise ProvideObjectError(f"Failed to load YAML config: {e}")
        return self
    
    def from_env(self, name, default=None, as_=None):
        """Load single value from environment variable."""
        value = os.getenv(name, default)
        if value is None:
            raise ProvideObjectError(f"Environment variable '{name}' not found")
        
        if as_ is not None:
            try:
                value = as_(value)
            except (ValueError, TypeError) as e:
                raise ProvideObjectError(f"Failed to convert env var '{name}': {e}")
        
        return value
    
    def get(self, key, default=None):
        """Get configuration value by key with optional default."""
        keys = key.split('.')
        data = self._data
        
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return data
    
    def set(self, key, value):
        """Set configuration value by key."""
        keys = key.split('.')
        data = self._data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
        return self


class ConfigurationOption(Provider):
    """Configuration option provider for accessing nested config values."""
    
    def __init__(self, name, root_config):
        super().__init__()
        self._name = name
        self._root = root_config
        self._children = {}
    
    def __getattr__(self, name):
        """Get nested configuration option."""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        full_name = f"{self._name}.{name}"
        if name not in self._children:
            self._children[name] = ConfigurationOption(full_name, self._root)
        return self._children[name]
    
    def __getitem__(self, key):
        """Get configuration option by key access."""
        return self.__getattr__(key)
    
    def _provide(self, args, kwargs):
        """Return the configuration value."""
        return self._root.get(self._name)
    
    def as_int(self):
        """Return configuration value as integer."""
        return TypedConfigurationOption(int, self)
    
    def as_float(self):
        """Return configuration value as float."""
        return TypedConfigurationOption(float, self)
    
    def as_bool(self):
        """Return configuration value as boolean."""
        def bool_converter(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        return TypedConfigurationOption(bool_converter, self)


class TypedConfigurationOption(Provider):
    """Configuration option with type conversion."""
    
    def __init__(self, converter, option):
        super().__init__()
        self._converter = converter
        self._option = option
    
    def _provide(self, args, kwargs):
        """Return the converted configuration value."""
        value = self._option()
        if value is None:
            return None
        
        try:
            return self._converter(value)
        except (ValueError, TypeError) as e:
            raise ProvideObjectError(f"Failed to convert config value: {e}")