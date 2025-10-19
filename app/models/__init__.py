"""
Data Models and Schemas

This package contains all Pydantic models, schemas, and data structures
used throughout the application.

Organized by:
- api.py: API request/response models
- tools.py: Tool input schemas for LangChain
- grist.py: Grist data structures (tables, columns, records)
- exceptions.py: Custom exception classes
- config.py: Application configuration
"""

# API Models
from app.models.api import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ToolCall,
    UIMessage,
)

# Configuration (imported from core for convenience)
from app.core.config import (
    Settings,
    settings,
    get_settings,
    is_development,
    is_production,
)

# Exceptions
from app.models.exceptions import (
    ChoiceValidationException,
    ColumnNotFoundException,
    ConfirmationRequiredException,
    GristAPIException,
    PermissionDeniedException,
    QueryException,
    RecordNotFoundException,
    ReferenceValidationException,
    TableNotFoundException,
    TypeMismatchException,
    ValidationException,
)

# Grist Data Models
from app.models.grist import (
    Column,
    ColumnFields,
    Record,
    Table,
    TableInfo,
)

# Tool Input Schemas
from app.models.tools import (
    AddRecordsInput,
    GetTableColumnsInput,
    QueryDocumentInput,
    UpdateRecordsInput,
)

# Confirmation Workflow
from app.models.confirmation import (
    ConfirmationDecision,
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationStatus,
    OperationPreview,
    OperationType,
)

__all__ = [
    # API Models
    "UIMessage",
    "ChatRequest",
    "ChatResponse",
    "ToolCall",
    "HealthResponse",
    # Configuration
    "Settings",
    "settings",
    "get_settings",
    "is_development",
    "is_production",
    # Exceptions
    "GristAPIException",
    "PermissionDeniedException",
    "TableNotFoundException",
    "ColumnNotFoundException",
    "ValidationException",
    "TypeMismatchException",
    "ChoiceValidationException",
    "ReferenceValidationException",
    "QueryException",
    "RecordNotFoundException",
    "ConfirmationRequiredException",
    # Grist Models
    "Table",
    "TableInfo",
    "Column",
    "ColumnFields",
    "Record",
    # Tool Schemas
    "GetTableColumnsInput",
    "QueryDocumentInput",
    "AddRecordsInput",
    "UpdateRecordsInput",
    # Confirmation
    "ConfirmationRequest",
    "ConfirmationResponse",
    "ConfirmationDecision",
    "ConfirmationStatus",
    "OperationPreview",
    "OperationType",
]
