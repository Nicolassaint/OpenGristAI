"""
Grist Service - Interface to Grist Document Engine

This service provides a high-level interface to interact with Grist documents.
Uses the GristAPIClient for actual API calls.
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.grist_client import GristAPIClient

logger = logging.getLogger(__name__)


class GristService:
    """
    High-level service for interacting with Grist documents.

    This service wraps the GristAPIClient and provides additional
    business logic, validation, and error handling.
    """

    def __init__(
        self,
        document_id: str,
        access_token: str,
        base_url: str = "https://docs.getgrist.com",
        enable_validation: bool = True,
        use_api_key: bool = False,
    ):
        """
        Initialize the Grist service.

        Args:
            document_id: Grist document ID or name
            access_token: API Key or JWT access token from Grist
            base_url: Base URL for Grist API
            enable_validation: Whether to enable validation (default: True)
            use_api_key: If True, use API Key auth. If False, use widget JWT token.
        """
        self.document_id = document_id
        self.access_token = access_token
        self.base_url = base_url
        self.enable_validation = enable_validation

        # Create API client
        self.client = GristAPIClient(
            document_id=document_id,
            access_token=access_token,
            base_url=base_url,
            use_api_key=use_api_key,
        )

        # Create validation service (lazy loaded)
        self._validator = None

        logger.info(f"GristService initialized for document: {document_id}")

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_validator(self):
        """Get or create the validation service."""
        if self._validator is None and self.enable_validation:
            from app.services.validation import ValidationService

            self._validator = ValidationService(self)
        return self._validator

    # ========================================================================
    # Table Operations
    # ========================================================================

    async def get_tables(self) -> List[Dict[str, Any]]:
        """
        Get all tables in the document.

        Returns:
            List of table objects with their IDs and metadata.
        """
        logger.info("Getting all tables")
        tables = await self.client.get_tables()
        logger.debug(f"Found {len(tables)} tables")
        return tables

    async def get_table_columns(self, table_id: str) -> List[Dict[str, Any]]:
        """
        Get all columns in a table.

        Args:
            table_id: The ID of the table

        Returns:
            List of column objects with their IDs, types, and metadata.

        Raises:
            ValueError: If table doesn't exist
        """
        logger.info(f"Getting columns for table '{table_id}'")

        try:
            columns = await self.client.get_table_columns(table_id)
            logger.debug(f"Found {len(columns)} columns in table '{table_id}'")
            return columns
        except Exception as e:
            logger.error(f"Error getting columns for table '{table_id}': {e}")
            raise ValueError(f"Table '{table_id}' not found or inaccessible")

    async def add_table(
        self, table_id: str, columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new table in the document via REST API.

        Args:
            table_id: ID for the new table
            columns: List of column definitions, each with 'id' and 'fields'
                     fields can contain: label, type, formula, widgetOptions, etc.

        Returns:
            Result with created table info

        Raises:
            ValidationException: If table_id or columns are invalid

        Example:
            columns = [
                {"id": "Name", "fields": {"label": "Name", "type": "Text"}},
                {"id": "Age", "fields": {"label": "Age", "type": "Int"}}
            ]
            await service.add_table("Students", columns)
        """
        logger.info(f"Creating table '{table_id}' with {len(columns)} column(s)")

        # Basic validation
        if not table_id or not table_id.strip():
            from app.models import ValidationException

            raise ValidationException("table_id", "Table ID cannot be empty")

        if not columns:
            from app.models import ValidationException

            raise ValidationException("columns", "At least one column is required")

        try:
            result = await self.client.add_table(table_id, columns)
            logger.debug(f"Created table '{table_id}'")
            return {"table_id": table_id, "columns_count": len(columns)}

        except Exception as e:
            logger.error(f"Error creating table '{table_id}': {e}")
            raise

    # ========================================================================
    # Column Operations
    # ========================================================================

    async def add_table_column(
        self,
        table_id: str,
        column_id: str,
        col_type: str,
        label: Optional[str] = None,
        formula: Optional[str] = None,
        widget_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a new column to a table via REST API.

        Args:
            table_id: Table ID
            column_id: Column ID
            col_type: Column type (Text, Numeric, Int, Bool, Date, DateTime, Choice, Ref, etc.)
            label: Column display label (optional, defaults to column_id)
            formula: Optional formula for computed columns
            widget_options: Optional widget configuration (e.g., choices for Choice columns)

        Returns:
            Result with created column info

        Raises:
            TableNotFoundException: If table doesn't exist
            ValidationException: If column parameters are invalid

        Example:
            # Simple text column
            await service.add_table_column("Students", "Email", "Text", label="Email Address")

            # Choice column with options
            await service.add_table_column(
                "Students",
                "Grade",
                "Choice",
                label="Grade Level",
                widget_options={"choices": ["A", "B", "C", "D", "F"]}
            )
        """
        logger.info(f"Adding column '{column_id}' to table '{table_id}'")

        # Validate table exists (get corrected ID for case-insensitive match)
        validator = self._get_validator()
        if validator:
            table_id = await validator.validate_table_exists(table_id)

        # Validate inputs
        if not column_id or not column_id.strip():
            from app.models import ValidationException

            raise ValidationException("column_id", "Column ID cannot be empty")

        try:
            # Build column fields dict
            fields = {"type": col_type}
            if label:
                fields["label"] = label
            if formula:
                fields["formula"] = formula
            if widget_options:
                fields["widgetOptions"] = widget_options

            await self.client.add_column(table_id, column_id, fields)
            logger.debug(f"Added column '{column_id}' to table '{table_id}'")

            return {"table_id": table_id, "column_id": column_id, "type": col_type}

        except Exception as e:
            logger.error(f"Error adding column to table '{table_id}': {e}")
            raise

    async def update_table_column(
        self,
        table_id: str,
        column_id: str,
        label: Optional[str] = None,
        col_type: Optional[str] = None,
        formula: Optional[str] = None,
        widget_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing column's properties via REST API.

        Args:
            table_id: Table ID
            column_id: Column ID to update
            label: New label (optional)
            col_type: New type (optional)
            formula: New formula (optional)
            widget_options: New widget options (optional)

        Returns:
            Result confirming the update

        Raises:
            TableNotFoundException: If table doesn't exist
            ColumnNotFoundException: If column doesn't exist
        """
        logger.info(f"Updating column '{column_id}' in table '{table_id}'")

        # Validate table and column exist (get corrected IDs for case-insensitive match)
        validator = self._get_validator()
        if validator:
            table_id = await validator.validate_table_exists(table_id)
            column_info = await validator.validate_column_exists(table_id, column_id)
            column_id = column_info["id"]  # Use corrected column ID

        try:
            # Build fields dict with updates
            fields = {}
            if label is not None:
                fields["label"] = label
            if col_type is not None:
                fields["type"] = col_type
            if formula is not None:
                fields["formula"] = formula
            if widget_options is not None:
                fields["widgetOptions"] = widget_options

            if not fields:
                from app.models import ValidationException

                raise ValidationException(
                    "updates", "At least one property must be updated"
                )

            await self.client.update_column(table_id, column_id, fields)
            logger.debug(f"Updated column '{column_id}' in table '{table_id}'")

            return {"table_id": table_id, "column_id": column_id, "updated": True}

        except Exception as e:
            logger.error(f"Error updating column '{column_id}': {e}")
            raise

    async def remove_table_column(
        self, table_id: str, column_id: str
    ) -> Dict[str, Any]:
        """
        Remove a column from a table via REST API.

        WARNING: This is a destructive operation and cannot be undone.
        All data in this column will be permanently deleted.

        Args:
            table_id: Table ID
            column_id: Column ID to remove

        Returns:
            Result confirming the deletion

        Raises:
            TableNotFoundException: If table doesn't exist
            ColumnNotFoundException: If column doesn't exist
        """
        logger.warning(f"Removing column '{column_id}' from table '{table_id}'")

        # Validate table and column exist (get corrected IDs for case-insensitive match)
        validator = self._get_validator()
        if validator:
            table_id = await validator.validate_table_exists(table_id)
            column_info = await validator.validate_column_exists(table_id, column_id)
            column_id = column_info["id"]  # Use corrected column ID

        try:
            await self.client.delete_column(table_id, column_id)
            logger.debug(f"Removed column '{column_id}' from table '{table_id}'")

            return {"table_id": table_id, "column_id": column_id, "deleted": True}

        except Exception as e:
            logger.error(f"Error removing column '{column_id}': {e}")
            raise

    # ========================================================================
    # Sample Data Operations
    # ========================================================================

    async def get_sample_records(
        self, table_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get sample records from a table to understand actual data values.

        This is particularly useful before generating SQL queries to see
        the actual values in columns (e.g., 'F'/'M' vs 'Homme'/'Femme').

        Args:
            table_id: Table ID
            limit: Number of sample records to return (default: 10, max: 10)

        Returns:
            List of sample records with their actual field values and IDs.
            Each record includes an 'id' field for targeting specific records.

        Raises:
            TableNotFoundException: If table doesn't exist
        """
        logger.info(f"Getting {limit} sample records from table '{table_id}'")

        # Validate table exists (get corrected ID for case-insensitive match)
        validator = self._get_validator()
        if validator:
            table_id = await validator.validate_table_exists(table_id)

        # Enforce max limit of 10 to prevent token overflow
        limit = min(limit, 10)

        try:
            records = await self.client.get_records(table_id, limit=limit)

            # Extract fields from each record and include the ID
            samples = []
            for record in records:
                # Grist records have structure: {"id": ..., "fields": {...}}
                if "fields" in record:
                    # Include the ID so the LLM knows which records to target
                    sample = record["fields"].copy()
                    sample["id"] = record["id"]
                    samples.append(sample)
                else:
                    # Fallback if structure is different
                    samples.append(record)

            logger.debug(
                f"Retrieved {len(samples)} sample records from table '{table_id}'"
            )
            return samples

        except Exception as e:
            logger.error(f"Error getting sample records from table '{table_id}': {e}")
            raise

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def query_document(
        self, query: str, args: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query against the document.
        Automatically limits results to 100 rows maximum to prevent token overflow.

        Args:
            query: SQL SELECT query
            args: Optional query arguments

        Returns:
            List of matching records (max 100 rows).
        """
        logger.info(f"Executing query: {query[:100]}...")

        try:
            results = await self.client.query_sql(query, args)

            # Apply hard limit of 100 rows to prevent token overflow
            if len(results) > 100:
                logger.warning(
                    f"Query returned {len(results)} records, limiting to 100 to prevent token overflow"
                )
                results = results[:100]

            logger.debug(f"Query returned {len(results)} records")
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    # ========================================================================
    # Record Operations
    # ========================================================================

    async def add_records(
        self, table_id: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add records to a table.

        Args:
            table_id: The ID of the table
            records: List of record objects to add

        Returns:
            Result with created record IDs.

        Raises:
            ValidationException: If validation fails
            TableNotFoundException: If table doesn't exist
        """
        logger.info(f"Adding {len(records)} record(s) to table '{table_id}'")

        # Validate if enabled (get corrected ID for case-insensitive match)
        validator = self._get_validator()
        corrected_records = records
        if validator:
            table_id = await validator.validate_table_exists(table_id)
            # Validate and correct each record
            corrected_records = []
            for record in records:
                corrected = await validator.validate_record_data(table_id, record)
                corrected_records.append(corrected)

        try:
            # Format records for Grist API
            # Grist expects {"fields": {...}} for each record
            formatted_records = []
            for record in corrected_records:
                formatted_records.append({"fields": record})

            result = await self.client.add_records(table_id, formatted_records)

            # Extract record IDs from response
            created_ids = [r["id"] for r in result.get("records", [])]
            logger.debug(f"Created {len(created_ids)} records")

            return {"record_ids": created_ids, "count": len(created_ids)}

        except Exception as e:
            logger.error(f"Error adding records to table '{table_id}': {e}")
            raise

    async def update_records(
        self, table_id: str, record_ids: List[int], records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update records in a table.

        Args:
            table_id: The ID of the table
            record_ids: List of record IDs to update
            records: List of record objects with updated values

        Returns:
            Result confirming the update.

        Raises:
            ValidationException: If validation fails
            TableNotFoundException: If table doesn't exist
        """
        logger.info(f"Updating {len(record_ids)} record(s) in table '{table_id}'")

        # Validate record counts match
        if len(record_ids) != len(records):
            from app.models import ValidationException

            raise ValidationException(
                "record_ids",
                f"Mismatch: {len(record_ids)} IDs but {len(records)} record objects",
            )

        # Validate if enabled (get corrected ID for case-insensitive match)
        validator = self._get_validator()
        corrected_records = records
        if validator:
            table_id = await validator.validate_table_exists(table_id)
            # Validate and correct each record
            corrected_records = []
            for record in records:
                corrected = await validator.validate_record_data(table_id, record)
                corrected_records.append(corrected)

        try:
            # Format records for Grist API
            # Grist expects {"id": ..., "fields": {...}} for each record
            formatted_records = []
            for record_id, fields in zip(record_ids, corrected_records):
                formatted_records.append({"id": record_id, "fields": fields})

            await self.client.update_records(table_id, formatted_records)
            logger.debug(f"Updated {len(record_ids)} records")

            return {"updated_count": len(record_ids)}

        except Exception as e:
            logger.error(f"Error updating records in table '{table_id}': {e}")
            raise

    async def remove_records(
        self, table_id: str, record_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Remove records from a table.

        Args:
            table_id: The ID of the table
            record_ids: List of record IDs to remove

        Returns:
            Result confirming the deletion.

        Raises:
            ValueError: If table doesn't exist
        """
        logger.warning(f"Removing {len(record_ids)} record(s) from table '{table_id}'")

        try:
            await self.client.delete_records(table_id, record_ids)
            logger.debug(f"Removed {len(record_ids)} records")

            return {"deleted_count": len(record_ids)}

        except Exception as e:
            logger.error(f"Error removing records from table '{table_id}': {e}")
            raise ValueError(f"Failed to remove records: {str(e)}")
