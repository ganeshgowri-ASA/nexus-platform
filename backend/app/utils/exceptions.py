"""Custom exceptions for the application"""


class NexusException(Exception):
    """Base exception for NEXUS platform"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OCRProcessingError(NexusException):
    """Exception raised when OCR processing fails"""
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message, status_code=400)


class TranslationError(NexusException):
    """Exception raised when translation fails"""
    def __init__(self, message: str = "Translation failed"):
        super().__init__(message, status_code=400)


class InvalidFileTypeError(NexusException):
    """Exception raised when file type is not supported"""
    def __init__(self, message: str = "Invalid file type"):
        super().__init__(message, status_code=400)


class FileSizeExceededError(NexusException):
    """Exception raised when file size exceeds limit"""
    def __init__(self, message: str = "File size exceeds limit"):
        super().__init__(message, status_code=413)


class LanguageNotSupportedError(NexusException):
    """Exception raised when language is not supported"""
    def __init__(self, message: str = "Language not supported"):
        super().__init__(message, status_code=400)


class APIKeyMissingError(NexusException):
    """Exception raised when required API key is missing"""
    def __init__(self, message: str = "Required API key is missing"):
        super().__init__(message, status_code=500)
