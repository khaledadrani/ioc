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