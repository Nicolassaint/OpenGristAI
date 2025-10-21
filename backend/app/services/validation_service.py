"""
Validation Service

Provides validation logic for Grist operations:
- Permission checks
- Schema validation (tables, columns exist)
- Type validation
- Choice/reference validation
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models import (
    ChoiceValidationException,
    ColumnNotFoundException,
    PermissionDeniedException,
    ReferenceValidationException,
    TableNotFoundException,
    TypeMismatchException,
    ValidationException,
)
from app.services.grist_service import GristService

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for validating Grist operations.

    Performs proactive validation before executing operations to:
    - Provide better error messages
    - Prevent invalid operations
    - Suggest corrections
    """

    def __init__(self, grist_service: GristService):
        """
        Initialize validation service.

        Args:
            grist_service: Grist service for schema queries
        """
        self.grist_service = grist_service
        self._tables_cache: Optional[List[Dict[str, Any]]] = None
        self._columns_cache: Dict[str, List[Dict[str, Any]]] = {}

    async def validate_table_exists(self, table_id: str) -> str:
        """
        Validate that a table exists (case-insensitive).

        Args:
            table_id: Table ID to check

        Returns:
            The correct table ID with proper casing

        Raises:
            TableNotFoundException: If table doesn't exist
        """
        if self._tables_cache is None:
            self._tables_cache = await self.grist_service.get_tables()

        table_ids = [t["id"] for t in self._tables_cache]

        # Exact match first
        if table_id in table_ids:
            logger.debug(f"Table '{table_id}' validated (exact match)")
            return table_id

        # Case-insensitive match
        table_id_lower = table_id.lower()
        for tid in table_ids:
            if tid.lower() == table_id_lower:
                logger.debug(f"Table '{table_id}' validated (case-insensitive match: '{tid}')")
                return tid

        raise TableNotFoundException(table_id, table_ids)

    async def validate_column_exists(
        self, table_id: str, column_id: str
    ) -> Dict[str, Any]:
        """
        Validate that a column exists in a table (case-insensitive).

        Args:
            table_id: Table ID
            column_id: Column ID to check

        Returns:
            Column metadata (with corrected column ID if case-insensitive match)

        Raises:
            ColumnNotFoundException: If column doesn't exist
        """
        # Ensure table exists first (and get correct casing)
        table_id = await self.validate_table_exists(table_id)

        # Get columns (use cache)
        if table_id not in self._columns_cache:
            self._columns_cache[table_id] = await self.grist_service.get_table_columns(
                table_id
            )

        columns = self._columns_cache[table_id]
        column_ids = [c["id"] for c in columns]

        # Exact match first
        column = next((c for c in columns if c["id"] == column_id), None)
        if column:
            logger.debug(f"Column '{column_id}' in table '{table_id}' validated (exact match)")
            return column

        # Case-insensitive match
        column_id_lower = column_id.lower()
        for c in columns:
            if c["id"].lower() == column_id_lower:
                logger.debug(f"Column '{column_id}' validated (case-insensitive match: '{c['id']}')")
                # Return column with corrected ID
                return c

        raise ColumnNotFoundException(column_id, table_id, column_ids)

    async def validate_record_data(
        self, table_id: str, record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate record data against table schema and correct field IDs.

        Args:
            table_id: Table ID
            record: Record data to validate

        Returns:
            Corrected record with proper field IDs (case-insensitive matching applied)

        Raises:
            ValidationException: If validation fails
        """
        # Get columns for the table
        if table_id not in self._columns_cache:
            self._columns_cache[table_id] = await self.grist_service.get_table_columns(
                table_id
            )

        columns = {c["id"]: c for c in self._columns_cache[table_id]}
        corrected_record = {}

        # Validate each field in the record
        for field_id, value in record.items():
            if field_id == "id":
                # Skip ID field (auto-generated)
                corrected_record["id"] = value
                continue

            # Try to find column (exact match first, then case-insensitive)
            column = None
            corrected_field_id = field_id

            if field_id in columns:
                # Exact match
                column = columns[field_id]
            else:
                # Try case-insensitive match
                column_info = await self.validate_column_exists(table_id, field_id)
                corrected_field_id = column_info["id"]
                column = column_info

            # Validate the field type
            await self._validate_field_type(corrected_field_id, value, column)

            # Add to corrected record with proper ID
            corrected_record[corrected_field_id] = value

        logger.debug(f"Record data for table '{table_id}' validated and corrected")
        return corrected_record

    async def _validate_field_type(
        self, field_id: str, value: Any, column: Dict[str, Any]
    ) -> None:
        """
        Validate that a field value matches the column type.

        Args:
            field_id: Field/column ID
            value: Value to validate
            column: Column metadata

        Raises:
            TypeMismatchException: If type doesn't match
            ChoiceValidationException: If choice value is invalid
            ReferenceValidationException: If reference is invalid
        """
        if value is None:
            # Null values are generally allowed
            return

        column_type = column.get("type", "Any")

        # Type validation based on Grist column types
        if column_type == "Text":
            if not isinstance(value, str):
                raise TypeMismatchException(
                    field_id, "Text", value, ["Convert to string"]
                )

        elif column_type == "Numeric":
            if not isinstance(value, (int, float)):
                raise TypeMismatchException(
                    field_id, "Numeric", value, ["Use a number instead"]
                )

        elif column_type == "Int":
            if not isinstance(value, int):
                if isinstance(value, float) and value.is_integer():
                    # Allow float that's actually an int
                    pass
                else:
                    raise TypeMismatchException(
                        field_id, "Int", value, ["Use an integer instead"]
                    )

        elif column_type == "Bool":
            if not isinstance(value, bool):
                raise TypeMismatchException(
                    field_id, "Bool", value, ["Use true or false"]
                )

        elif column_type in ["Date", "DateTime"]:
            # Grist expects Unix timestamp in seconds
            if not isinstance(value, (int, float)):
                raise TypeMismatchException(
                    field_id,
                    "Date/DateTime",
                    value,
                    ["Use Unix timestamp in seconds"],
                )

        elif column_type == "Choice":
            # Validate against allowed choices
            allowed_choices = column.get("widgetOptions", {}).get("choices", [])
            if allowed_choices and value not in allowed_choices:
                raise ChoiceValidationException(field_id, value, allowed_choices)

        elif column_type == "ChoiceList":
            # Must be a list with "L" prefix
            if not isinstance(value, list):
                raise TypeMismatchException(
                    field_id, "ChoiceList", value, ['Use format ["L", "Choice1", ...]']
                )
            if len(value) == 0 or value[0] != "L":
                raise ValidationException(
                    field_id,
                    "ChoiceList must start with 'L'",
                    ['Use format ["L", "Choice1", "Choice2"]'],
                )

            # Validate each choice
            allowed_choices = column.get("widgetOptions", {}).get("choices", [])
            if allowed_choices:
                for choice in value[1:]:  # Skip "L"
                    if choice not in allowed_choices:
                        raise ChoiceValidationException(
                            field_id, choice, allowed_choices
                        )

        elif column_type == "Ref":
            # Must be an integer (record ID)
            if not isinstance(value, int):
                raise TypeMismatchException(
                    field_id, "Ref", value, ["Use record ID (integer)"]
                )

            # TODO: Optionally validate that record exists in referenced table
            # referenced_table = column.get("widgetOptions", {}).get("refTable")

        elif column_type == "RefList":
            # Must be a list with "L" prefix
            if not isinstance(value, list):
                raise TypeMismatchException(
                    field_id, "RefList", value, ['Use format ["L", id1, id2, ...]']
                )
            if len(value) == 0 or value[0] != "L":
                raise ValidationException(
                    field_id,
                    "RefList must start with 'L'",
                    ['Use format ["L", 1, 2, 3]'],
                )

            # Validate each ID is an integer
            for ref_id in value[1:]:  # Skip "L"
                if not isinstance(ref_id, int):
                    raise TypeMismatchException(
                        field_id,
                        "RefList",
                        ref_id,
                        ["All IDs must be integers"],
                    )

        elif column_type == "Attachments":
            # Same as RefList
            if not isinstance(value, list):
                raise TypeMismatchException(
                    field_id, "Attachments", value, ['Use format ["L", id1, id2, ...]']
                )
            if len(value) > 0 and value[0] != "L":
                raise ValidationException(
                    field_id,
                    "Attachments list must start with 'L'",
                    ['Use format ["L", 1, 2, 3]'],
                )

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._tables_cache = None
        self._columns_cache = {}
        logger.debug("Validation cache cleared")


# TODO: Add more validation
# - Validate that referenced records exist
# - Validate formula syntax
# - Validate widget options
# - Validate access rules

# TODO: Add smart suggestions
# - Fuzzy match table/column names
# - Suggest similar choices for typos
# - Auto-convert compatible types (string -> int, etc.)
