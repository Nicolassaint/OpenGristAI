"""
Error Handler Middleware

Centralized error handling for FastAPI.
Converts exceptions into user-friendly API responses.
"""

import logging
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError

from app.middleware.exceptions import (
    ChoiceValidationException,
    ColumnNotFoundException,
    ConfirmationRequiredException,
    GristAPIException,
    PermissionDeniedException,
    QueryException,
    RecordNotFoundException,
    TableNotFoundException,
    TypeMismatchException,
    ValidationException,
)

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    message: str,
    error_type: str,
    details: dict = None,
    suggestions: list = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        message: Error message
        error_type: Type of error
        details: Additional error details
        suggestions: Suggestions for fixing the error

    Returns:
        JSONResponse with error information
    """
    content = {
        "error": {
            "type": error_type,
            "message": message,
            "details": details or {},
        }
    }

    if suggestions:
        content["error"]["suggestions"] = suggestions

    return JSONResponse(status_code=status_code, content=content)


async def grist_exception_handler(
    request: Request, exc: GristAPIException
) -> JSONResponse:
    """
    Handle Grist-specific exceptions.

    Args:
        request: FastAPI request
        exc: Grist exception

    Returns:
        JSON error response
    """
    logger.warning(f"Grist exception: {exc.message}", exc_info=True)

    # Map specific exceptions to HTTP status codes
    if isinstance(exc, PermissionDeniedException):
        return create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            message=exc.message,
            error_type="permission_denied",
            details={
                "operation": exc.operation,
                "required_access": exc.required_access,
            },
            suggestions=[
                "Enable 'Full document access' in widget settings",
                "Check document access rules",
            ],
        )

    elif isinstance(exc, TableNotFoundException):
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=exc.message,
            error_type="table_not_found",
            details={"table_id": exc.table_id},
            suggestions=[
                "Check table name spelling",
                "Use get_tables() to list available tables",
            ],
        )

    elif isinstance(exc, ColumnNotFoundException):
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=exc.message,
            error_type="column_not_found",
            details={"table_id": exc.table_id, "column_id": exc.column_id},
            suggestions=[
                "Check column name spelling",
                "Use get_table_columns() to list available columns",
                "Use column IDs, not labels",
            ],
        )

    elif isinstance(exc, RecordNotFoundException):
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=exc.message,
            error_type="record_not_found",
            details={"table_id": exc.table_id, "record_ids": exc.record_ids},
            suggestions=[
                "Verify record IDs exist",
                "Use query_document() to find valid record IDs",
            ],
        )

    elif isinstance(exc, ChoiceValidationException):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_type="invalid_choice",
            details={"column_id": exc.field, "value": exc.value},
            suggestions=exc.allowed_choices,
        )

    elif isinstance(exc, TypeMismatchException):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_type="type_mismatch",
            details={
                "column_id": exc.field,
                "expected_type": exc.expected_type,
                "actual_value": str(exc.actual_value),
            },
            suggestions=exc.suggestions,
        )

    elif isinstance(exc, ValidationException):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_type="validation_error",
            details={"field": exc.field, "reason": exc.reason},
            suggestions=exc.suggestions,
        )

    elif isinstance(exc, QueryException):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_type="query_error",
            details={"query": exc.query, "error": exc.error_message},
            suggestions=[
                "Check SQL syntax",
                "Ensure table and column names are correct",
                "Only SQLite-compatible SQL is supported",
            ],
        )

    elif isinstance(exc, ConfirmationRequiredException):
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            message=exc.message,
            error_type="confirmation_required",
            details={
                "operation": exc.operation,
                "affected_items": exc.affected_items,
                "preview": exc.preview_data,
            },
            suggestions=[
                "Review the preview data",
                "Confirm the operation explicitly",
            ],
        )

    # Generic Grist exception
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=exc.message,
        error_type="grist_error",
        details=exc.details,
    )


async def httpx_exception_handler(
    request: Request, exc: HTTPStatusError
) -> JSONResponse:
    """
    Handle HTTP exceptions from Grist API calls.

    Args:
        request: FastAPI request
        exc: HTTP status error

    Returns:
        JSON error response
    """
    logger.error(f"HTTP error calling Grist API: {exc}", exc_info=True)

    status_code = exc.response.status_code

    # Map Grist API errors to user-friendly messages
    if status_code == 401:
        message = "Authentication failed. The Grist access token may have expired."
        suggestions = ["Refresh the page to get a new token", "Check document access"]
    elif status_code == 403:
        message = "Permission denied. You don't have access to perform this operation."
        suggestions = ["Enable 'Full document access' in widget settings"]
    elif status_code == 404:
        message = "Resource not found. The document, table, or record doesn't exist."
        suggestions = ["Verify document ID", "Check that the resource exists"]
    elif status_code == 429:
        message = "Rate limit exceeded. Too many requests to Grist API."
        suggestions = ["Wait a moment and try again", "Reduce request frequency"]
    else:
        message = f"Grist API error: {exc.response.text}"
        suggestions = []

    return create_error_response(
        status_code=status_code,
        message=message,
        error_type="grist_api_error",
        details={"status_code": status_code, "response": exc.response.text[:200]},
        suggestions=suggestions,
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again.",
        error_type="internal_error",
        details={"exception": str(exc)},
        suggestions=[
            "Check your request format",
            "Try again in a moment",
            "Contact support if the problem persists",
        ],
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(GristAPIException, grist_exception_handler)
    app.add_exception_handler(HTTPStatusError, httpx_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
