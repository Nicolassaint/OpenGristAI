"""
Grist Data Models

Pydantic models representing Grist data structures (tables, columns, records).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TableInfo(BaseModel):
    """Information about a table in a Grist document."""

    id: str = Field(..., description="Table ID")
    label: Optional[str] = Field(default=None, description="Table display label")


class Table(BaseModel):
    """Complete table data with metadata."""

    id: str = Field(..., description="Table ID")
    label: Optional[str] = Field(default=None, description="Table display label")
    columns: Optional[List["Column"]] = Field(
        default=None, description="List of columns in the table"
    )


class ColumnFields(BaseModel):
    """Column field properties."""

    type: str = Field(..., description="Column type (Text, Numeric, Int, Bool, etc.)")
    label: Optional[str] = Field(default=None, description="Column display label")
    formula: Optional[str] = Field(default=None, description="Formula for computed columns")
    widgetOptions: Optional[Dict[str, Any]] = Field(
        default=None, description="Widget configuration options"
    )


class Column(BaseModel):
    """Column definition in a Grist table."""

    id: str = Field(..., description="Column ID")
    fields: ColumnFields = Field(..., description="Column field properties")


class Record(BaseModel):
    """A single record in a Grist table."""

    id: int = Field(..., description="Record ID (row ID)")
    fields: Dict[str, Any] = Field(..., description="Record field values")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "fields": {
                    "Name": "John Doe",
                    "Age": 30,
                    "Email": "john@example.com",
                },
            }
        }
