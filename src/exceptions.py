"""Custom exceptions for the Data-Sorter pipeline."""


class FileFormatError(Exception):
    """Raised when the input file format is unsupported or corrupted."""


class ColumnDetectionError(Exception):
    """Raised when required columns cannot be detected in the input."""


class ConfigError(Exception):
    """Raised when configuration files are missing or malformed."""
