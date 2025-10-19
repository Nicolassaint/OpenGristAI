"""
Tool Input Schemas

Pydantic models for validating tool inputs in LangChain.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GetTableColumnsInput(BaseModel):
    """Input for get_table_columns tool."""

    table_id: str = Field(..., description="The ID of the table")


class QueryDocumentInput(BaseModel):
    """Input for query_document tool."""

    query: str = Field(..., description="The SQL SELECT query to execute")
    args: Optional[List[Any]] = Field(
        default=None,
        description="Optional list of arguments for parameterized queries",
    )


class AddRecordsInput(BaseModel):
    """Input for add_records tool."""

    table_id: str = Field(..., description="The ID of the table to add records to")
    records: List[Dict[str, Any]] = Field(
        ..., description="List of record objects to add"
    )


class UpdateRecordsInput(BaseModel):
    """Input for update_records tool."""

    table_id: str = Field(..., description="The ID of the table to update records in")
    record_ids: List[int] = Field(..., description="List of record IDs to update")
    records: List[Dict[str, Any]] = Field(
        ..., description="List of record objects with updated values"
    )
