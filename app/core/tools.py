"""
Grist Tools for LangChain Agent

This module defines the tools that the LLM can use to interact with Grist documents.
For Phase 1, we implement 5 core tools:
- get_tables
- get_table_columns
- query_document
- add_records
- update_records

Note: Tools receive the GristService instance via a context variable set by the agent.
"""

from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.services.grist_service import GristService

# Context variable to store the current Grist service instance
_grist_service: ContextVar[Optional[GristService]] = ContextVar(
    "_grist_service", default=None
)


def set_grist_service(service: GristService) -> None:
    """Set the Grist service for the current context."""
    _grist_service.set(service)


def get_grist_service() -> GristService:
    """Get the Grist service for the current context."""
    service = _grist_service.get()
    if service is None:
        raise RuntimeError("GristService not configured. Call set_grist_service() first.")
    return service


# ============================================================================
# Input Schemas (Pydantic models for validation)
# ============================================================================


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


# ============================================================================
# Tool Definitions (Async)
# ============================================================================


@tool
async def get_tables() -> List[Dict[str, Any]]:
    """
    Returns all tables in a Grist document.

    Returns:
        List of table objects with their IDs and metadata.
    """
    service = get_grist_service()
    return await service.get_tables()


@tool
async def get_table_columns(table_id: str) -> List[Dict[str, Any]]:
    """
    Returns all columns in a table.

    Args:
        table_id: The ID of the table

    Returns:
        List of column objects with their IDs, types, and metadata.
    """
    service = get_grist_service()
    return await service.get_table_columns(table_id)


@tool
async def query_document(query: str, args: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Runs a SQL SELECT query against a Grist document and returns matching rows.
    Only SQLite-compatible SQL is supported.

    Args:
        query: The SQL SELECT query to execute
        args: Optional list of arguments for parameterized queries

    Returns:
        List of matching rows as dictionaries.
    """
    service = get_grist_service()
    return await service.query_document(query, args)


@tool
async def add_records(table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Adds one or more records to a table.

    IMPORTANT: Always use column IDs, not labels. Do not set the 'id' column.

    Args:
        table_id: The ID of the table to add records to
        records: List of record objects to add (dict with column_id: value)

    Returns:
        Result object with created record IDs.
    """
    service = get_grist_service()
    return await service.add_records(table_id, records)


@tool
async def update_records(
    table_id: str, record_ids: List[int], records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Updates one or more records in a table.

    IMPORTANT: Always use column IDs, not labels. Never modify the 'id' column.

    Args:
        table_id: The ID of the table to update records in
        record_ids: List of record IDs to update
        records: List of record objects with updated values (same length as record_ids)

    Returns:
        Result object confirming the update.
    """
    service = get_grist_service()
    return await service.update_records(table_id, record_ids, records)


@tool
async def remove_records(table_id: str, record_ids: List[int]) -> Dict[str, Any]:
    """
    Removes one or more records from a table.

    WARNING: This is a destructive operation and cannot be undone.

    IMPORTANT: Always confirm with the user before removing records.

    Args:
        table_id: The ID of the table to remove records from
        record_ids: List of record IDs to remove

    Returns:
        Result object confirming the deletion.
    """
    service = get_grist_service()
    return await service.remove_records(table_id, record_ids)


# ============================================================================
# Table Management Tools
# ============================================================================


@tool
async def add_table(table_id: str, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates a new table in the document via REST API.

    Each column must have:
    - id: Column ID (e.g., "Name", "Age")
    - fields: Object with column properties
      - type: Column type (Text, Numeric, Int, Bool, Date, DateTime, Choice, Ref, etc.)
      - label: Display label (optional, defaults to column id)
      - formula: Formula for computed columns (optional)
      - widgetOptions: Configuration for widgets (optional)

    Args:
        table_id: ID for the new table (e.g., "Students", "Projects")
        columns: List of column definitions with id and fields

    Returns:
        Result object with created table info.

    Example:
        columns = [
            {"id": "Name", "fields": {"type": "Text", "label": "Full Name"}},
            {"id": "Age", "fields": {"type": "Int", "label": "Age"}}
        ]
        add_table("Students", columns)
    """
    service = get_grist_service()
    return await service.add_table(table_id, columns)


# ============================================================================
# Column Management Tools
# ============================================================================


@tool
async def add_table_column(
    table_id: str,
    column_id: str,
    col_type: str,
    label: Optional[str] = None,
    formula: Optional[str] = None,
    widget_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Adds a new column to an existing table via REST API.

    Supported column types:
    - Text: Plain text
    - Numeric: Decimal numbers
    - Int: Integers
    - Bool: True/False
    - Date: Dates (stored as timestamps)
    - DateTime: Dates with time
    - Choice: Single choice from a list
    - ChoiceList: Multiple choices from a list
    - Ref: Reference to another table
    - RefList: References to multiple records

    Args:
        table_id: Table ID to add the column to
        column_id: ID for the new column (e.g., "Email", "Age")
        col_type: Column type (Text, Numeric, Int, Bool, Date, Choice, Ref, etc.)
        label: Display label for the column (optional, defaults to column_id)
        formula: Optional formula for computed columns (e.g., "$Age * 2")
        widget_options: Optional configuration (e.g., {"choices": ["A", "B"]} for Choice)

    Returns:
        Result object with created column info.

    Example:
        # Simple text column
        add_table_column("Students", "Email", "Text", label="Email Address")

        # Choice column
        add_table_column(
            "Students",
            "Grade",
            "Choice",
            label="Grade Level",
            widget_options={"choices": ["A", "B", "C", "D", "F"]}
        )
    """
    service = get_grist_service()
    return await service.add_table_column(
        table_id, column_id, col_type, label, formula, widget_options
    )


@tool
async def update_table_column(
    table_id: str,
    column_id: str,
    label: Optional[str] = None,
    col_type: Optional[str] = None,
    formula: Optional[str] = None,
    widget_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Updates an existing column's properties via REST API.

    You can update any combination of: label, type, formula, or widget options.
    At least one property must be specified.

    WARNING: Changing column type may cause data loss if values cannot be converted.

    Args:
        table_id: Table ID
        column_id: Column ID to update
        label: New display label (optional)
        col_type: New column type (optional)
        formula: New formula (optional, set to empty string to remove formula)
        widget_options: New widget configuration (optional)

    Returns:
        Result object confirming the update.
    """
    service = get_grist_service()
    return await service.update_table_column(
        table_id, column_id, label, col_type, formula, widget_options
    )


@tool
async def remove_table_column(table_id: str, column_id: str) -> Dict[str, Any]:
    """
    Removes a column from a table via REST API.

    WARNING: This is a destructive operation and cannot be undone.
    All data in this column will be permanently deleted.

    IMPORTANT: Always confirm with the user before removing a column.

    Args:
        table_id: Table ID
        column_id: Column ID to remove

    Returns:
        Result object confirming the deletion.
    """
    service = get_grist_service()
    return await service.remove_table_column(table_id, column_id)


# ============================================================================
# Utility Tools
# ============================================================================


@tool
async def get_grist_access_rules_reference() -> str:
    """
    Returns a reference guide for Grist access rules and permissions.

    Use this when the user asks about:
    - Access rules
    - Permissions
    - Document sharing
    - User roles

    Returns:
        Reference documentation for Grist access rules.
    """
    return """
Grist Access Rules Reference:

OVERVIEW:
Grist uses access rules to control who can view, edit, or manage documents.
Access rules can be applied at the document, table, or column level.

ACCESS LEVELS:
- Owners: Full control (can manage sharing and access rules)
- Editors: Can edit data and structure
- Viewers: Can view data (read-only)

CREATING ACCESS RULES:
Access rules are defined in the "Access Rules" section of document settings.
Rules use formulas to determine when they apply.

COMMON PATTERNS:
1. Restrict access by user:
   user.Email == "user@example.com"

2. Restrict by role:
   user.Role == "Manager"

3. Restrict to record owner:
   rec.Owner == user.Email

4. Allow if condition:
   rec.Status != "Confidential"

BEST PRACTICES:
- Test access rules with different users
- Start with simple rules and refine
- Document your access rules
- Use the "View As" feature to test

For detailed documentation, visit:
https://support.getgrist.com/access-rules/
    """


@tool
async def get_available_custom_widgets() -> List[Dict[str, str]]:
    """
    Returns a list of available custom widgets that can be used in Grist.

    Custom widgets extend Grist's functionality with interactive visualizations,
    forms, and integrations.

    Returns:
        List of available custom widgets with their names and descriptions.
    """
    return [
        {
            "name": "Calendar",
            "url": "https://gristlabs.github.io/grist-widget/calendar/",
            "description": "Display records in a calendar view"
        },
        {
            "name": "Map",
            "url": "https://gristlabs.github.io/grist-widget/map/",
            "description": "Display records on an interactive map"
        },
        {
            "name": "Chart",
            "url": "https://gristlabs.github.io/grist-widget/chart/",
            "description": "Create interactive charts and graphs"
        },
        {
            "name": "Timeline",
            "url": "https://gristlabs.github.io/grist-widget/timeline/",
            "description": "Visualize data on a timeline"
        },
        {
            "name": "Kanban",
            "url": "https://gristlabs.github.io/grist-widget/kanban/",
            "description": "Organize records in a Kanban board"
        },
    ]


# ============================================================================
# Tool Registry
# ============================================================================


def get_all_tools() -> List:
    """
    Returns all available tools for the agent.

    Total: 12 tools using documented Grist REST API endpoints only.

    Returns:
        List of tool functions.
    """
    return [
        # Table inspection (2 tools)
        get_tables,
        get_table_columns,

        # Query (1 tool)
        query_document,

        # Record operations (3 tools)
        add_records,
        update_records,
        remove_records,

        # Table management via REST API (1 tool)
        add_table,

        # Column management via REST API (3 tools)
        add_table_column,
        update_table_column,
        remove_table_column,

        # Utilities (2 tools)
        get_grist_access_rules_reference,
        get_available_custom_widgets,
    ]
