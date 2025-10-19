"""
Confirmation Workflow Models

Models for handling destructive operations that require user confirmation.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """Types of operations that may require confirmation."""

    DELETE_RECORDS = "delete_records"
    DELETE_COLUMN = "delete_column"
    UPDATE_RECORDS = "update_records"
    UPDATE_COLUMN_TYPE = "update_column_type"
    TRUNCATE_TABLE = "truncate_table"


class ConfirmationStatus(str, Enum):
    """Status of a confirmation request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OperationPreview(BaseModel):
    """Preview of what will be affected by an operation."""

    operation_type: OperationType
    description: str = Field(..., description="Human-readable description of the operation")
    affected_count: int = Field(..., description="Number of items that will be affected")
    affected_items: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Preview of items that will be affected (max 10)"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Warnings about this operation"
    )
    is_reversible: bool = Field(
        default=False, description="Whether this operation can be undone"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "operation_type": "delete_records",
                "description": "Delete 15 records from table 'Students'",
                "affected_count": 15,
                "affected_items": [
                    {"id": 1, "Name": "John Doe", "Age": 20},
                    {"id": 2, "Name": "Jane Smith", "Age": 21},
                ],
                "warnings": [
                    "This operation is irreversible",
                    "Referenced records in 'Projects' table may be affected",
                ],
                "is_reversible": False,
            }
        }


class ConfirmationRequest(BaseModel):
    """Request for user confirmation of a destructive operation."""

    confirmation_id: str = Field(..., description="Unique ID for this confirmation request")
    preview: OperationPreview
    tool_name: str = Field(..., description="Name of the tool to execute")
    tool_args: Dict[str, Any] = Field(..., description="Arguments for the tool")
    expires_in_seconds: int = Field(
        default=300, description="How long this confirmation is valid (default: 5 minutes)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "confirmation_id": "conf_abc123",
                "preview": {
                    "operation_type": "delete_records",
                    "description": "Delete 15 records from 'Students'",
                    "affected_count": 15,
                    "warnings": ["This operation is irreversible"],
                },
                "tool_name": "remove_records",
                "tool_args": {"table_id": "Students", "record_ids": [1, 2, 3]},
                "expires_in_seconds": 300,
            }
        }


class ConfirmationResponse(BaseModel):
    """Response to a confirmation request."""

    confirmation_id: str
    status: ConfirmationStatus
    message: str = Field(..., description="Message to display to the user")
    result: Optional[Any] = Field(
        default=None, description="Result of the operation if approved and executed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "confirmation_id": "conf_abc123",
                "status": "approved",
                "message": "Operation completed successfully",
                "result": {"deleted_count": 15},
            }
        }


class ConfirmationDecision(BaseModel):
    """User's decision on a confirmation request."""

    confirmation_id: str
    approved: bool = Field(..., description="Whether the user approved the operation")
    reason: Optional[str] = Field(
        default=None, description="Optional reason for the decision"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "confirmation_id": "conf_abc123",
                "approved": True,
                "reason": "Confirmed deletion of test records",
            }
        }
