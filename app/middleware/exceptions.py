"""
Custom Exception Classes

Defines specific exceptions for better error handling and user feedback.
"""

from typing import Any, Dict, Optional


class GristAPIException(Exception):
    """Base exception for all Grist-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PermissionDeniedException(GristAPIException):
    """Raised when user doesn't have required permissions."""

    def __init__(
        self,
        operation: str,
        required_access: str = "full",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = (
            f"Permission denied: '{operation}' requires '{required_access}' access. "
            f"Please enable 'Full document access' in widget settings."
        )
        super().__init__(message, details)
        self.operation = operation
        self.required_access = required_access


class TableNotFoundException(GristAPIException):
    """Raised when a table doesn't exist."""

    def __init__(self, table_id: str, available_tables: Optional[list] = None):
        message = f"Table '{table_id}' not found."
        if available_tables:
            message += f" Available tables: {', '.join(available_tables)}"
        super().__init__(message, {"table_id": table_id})
        self.table_id = table_id


class ColumnNotFoundException(GristAPIException):
    """Raised when a column doesn't exist."""

    def __init__(
        self, column_id: str, table_id: str, available_columns: Optional[list] = None
    ):
        message = f"Column '{column_id}' not found in table '{table_id}'."
        if available_columns:
            message += f" Available columns: {', '.join(available_columns)}"
        super().__init__(message, {"table_id": table_id, "column_id": column_id})
        self.table_id = table_id
        self.column_id = column_id


class ValidationException(GristAPIException):
    """Raised when data validation fails."""

    def __init__(self, field: str, reason: str, suggestions: Optional[list] = None):
        message = f"Validation error for '{field}': {reason}"
        if suggestions:
            message += f". Suggestions: {', '.join(suggestions)}"
        super().__init__(message, {"field": field, "reason": reason})
        self.field = field
        self.reason = reason
        self.suggestions = suggestions or []


class TypeMismatchException(ValidationException):
    """Raised when a value doesn't match the expected column type."""

    def __init__(
        self,
        column_id: str,
        expected_type: str,
        actual_value: Any,
        suggestions: Optional[list] = None,
    ):
        reason = f"Expected type '{expected_type}', got '{type(actual_value).__name__}'"
        super().__init__(column_id, reason, suggestions)
        self.expected_type = expected_type
        self.actual_value = actual_value


class ChoiceValidationException(ValidationException):
    """Raised when a choice value is not in the allowed list."""

    def __init__(self, column_id: str, value: str, allowed_choices: list):
        reason = f"Value '{value}' is not in allowed choices"
        super().__init__(column_id, reason, allowed_choices)
        self.value = value
        self.allowed_choices = allowed_choices


class ReferenceValidationException(ValidationException):
    """Raised when a reference points to a non-existent record."""

    def __init__(self, column_id: str, record_id: int, referenced_table: str):
        reason = f"Record ID {record_id} not found in table '{referenced_table}'"
        super().__init__(column_id, reason)
        self.record_id = record_id
        self.referenced_table = referenced_table


class QueryException(GristAPIException):
    """Raised when a SQL query fails."""

    def __init__(self, query: str, error_message: str):
        message = f"Query failed: {error_message}"
        super().__init__(message, {"query": query})
        self.query = query
        self.error_message = error_message


class RecordNotFoundException(GristAPIException):
    """Raised when a record doesn't exist."""

    def __init__(self, table_id: str, record_ids: list):
        message = f"Records not found in table '{table_id}': {', '.join(map(str, record_ids))}"
        super().__init__(message, {"table_id": table_id, "record_ids": record_ids})
        self.table_id = table_id
        self.record_ids = record_ids


class ConfirmationRequiredException(GristAPIException):
    """Raised when a destructive operation requires user confirmation."""

    def __init__(
        self,
        operation: str,
        affected_items: int,
        preview_data: Optional[Dict[str, Any]] = None,
    ):
        message = (
            f"Confirmation required: '{operation}' will affect {affected_items} item(s). "
            f"Please confirm this action."
        )
        super().__init__(message, {"preview": preview_data})
        self.operation = operation
        self.affected_items = affected_items
        self.preview_data = preview_data or {}
