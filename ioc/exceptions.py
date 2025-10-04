class GenericException(Exception):
    def __init__(self, message: str = "An Unexpected Error!", metadata: dict = None):
        super().__init__(message)
        self.message = message
        self.metadata = metadata

    def __str__(self):
        return self.message


class ProvideObjectError(GenericException):
    def __init__(self, message: str = "Unable to provide object!", metadata: dict = None):
        super().__init__(message, metadata)

class ProvideObjectAttributeError(GenericException):
    def __init__(self, message: str = "Unable to provide this object attribute!", metadata: dict = None):
        super().__init__(message, metadata)


class ConventionInjectionError(ProvideObjectError):
    def __init__(self, message: str = "Convention-based injection failed!", metadata: dict = None):
        super().__init__(message, metadata)


class ConfigurationNotLoadedError(ProvideObjectError):
    def __init__(self, config_key: str, provider_name: str = None):
        if provider_name:
            message = f"Configuration key '{config_key}' not found. Provider '{provider_name}' requires configuration to be loaded first. Call container.config.from_dict() or container.config.from_json() before accessing providers."
        else:
            message = f"Configuration key '{config_key}' not found. Load configuration first with container.config.from_dict() or container.config.from_json()."
        super().__init__(message)