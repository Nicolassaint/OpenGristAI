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
    ):
        """
        Initialize the Grist service.

        Args:
            document_id: Grist document ID or name
            access_token: JWT access token from Grist
            base_url: Base URL for Grist API
            enable_validation: Whether to enable validation (default: True)
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
        Create a new table in the document.

        Args:
            table_id: ID for the new table
            columns: List of column definitions, each with 'id', 'label', and 'type'

        Returns:
            Result with created table info

        Raises:
            ValidationException: If table_id or columns are invalid

        Example:
            columns = [
                {"id": "Name", "label": "Name", "type": "Text"},
                {"id": "Age", "label": "Age", "type": "Int"}
            ]
            await service.add_table("Students", columns)
        """
        logger.info(f"Creating table '{table_id}' with {len(columns)} column(s)")

        # Basic validation
        if not table_id or not table_id.strip():
            from app.middleware.exceptions import ValidationException
            raise ValidationException("table_id", "Table ID cannot be empty")

        if not columns:
            from app.middleware.exceptions import ValidationException
            raise ValidationException("columns", "At least one column is required")

        try:
            result = await self.client.add_table(table_id, columns)
            logger.debug(f"Created table '{table_id}'")
            return {"table_id": table_id, "columns_count": len(columns)}

        except Exception as e:
            logger.error(f"Error creating table '{table_id}': {e}")
            raise

    async def rename_table(self, table_id: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a table.

        Args:
            table_id: Current table ID
            new_name: New table ID/name

        Returns:
            Result confirming the rename

        Raises:
            TableNotFoundException: If table doesn't exist
            ValidationException: If new_name is invalid
        """
        logger.info(f"Renaming table '{table_id}' to '{new_name}'")

        # Validate new name
        if not new_name or not new_name.strip():
            from app.middleware.exceptions import ValidationException
            raise ValidationException("new_name", "New table name cannot be empty")

        # Validate table exists
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)

        try:
            await self.client.update_table(table_id, name=new_name)
            logger.debug(f"Renamed table '{table_id}' to '{new_name}'")
            return {"old_name": table_id, "new_name": new_name}

        except Exception as e:
            logger.error(f"Error renaming table '{table_id}': {e}")
            raise

    async def remove_table(self, table_id: str) -> Dict[str, Any]:
        """
        Remove a table from the document.

        WARNING: This is a destructive operation and cannot be undone.

        Args:
            table_id: Table ID to remove

        Returns:
            Result confirming the deletion

        Raises:
            TableNotFoundException: If table doesn't exist
        """
        logger.warning(f"Removing table '{table_id}'")

        # Validate table exists
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)

        try:
            await self.client.delete_table(table_id)
            logger.debug(f"Removed table '{table_id}'")
            return {"table_id": table_id, "deleted": True}

        except Exception as e:
            logger.error(f"Error removing table '{table_id}': {e}")
            raise

    # ========================================================================
    # Column Operations
    # ========================================================================

    async def add_table_column(
        self,
        table_id: str,
        column_id: str,
        label: str,
        col_type: str,
        formula: Optional[str] = None,
        widget_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a new column to a table.

        Args:
            table_id: Table ID
            column_id: Column ID
            label: Column display label
            col_type: Column type (Text, Numeric, Int, Bool, Date, DateTime, Choice, Ref, etc.)
            formula: Optional formula for computed columns
            widget_options: Optional widget configuration (e.g., choices for Choice columns)

        Returns:
            Result with created column info

        Raises:
            TableNotFoundException: If table doesn't exist
            ValidationException: If column parameters are invalid

        Example:
            # Simple text column
            await service.add_table_column("Students", "Email", "Email Address", "Text")

            # Choice column with options
            await service.add_table_column(
                "Students",
                "Grade",
                "Grade Level",
                "Choice",
                widget_options={"choices": ["A", "B", "C", "D", "F"]}
            )
        """
        logger.info(f"Adding column '{column_id}' to table '{table_id}'")

        # Validate table exists
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)

        # Validate inputs
        if not column_id or not column_id.strip():
            from app.middleware.exceptions import ValidationException
            raise ValidationException("column_id", "Column ID cannot be empty")

        try:
            kwargs = {}
            if formula:
                kwargs["formula"] = formula
            if widget_options:
                kwargs["widgetOptions"] = widget_options

            await self.client.add_column(table_id, column_id, label, col_type, **kwargs)
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
        Update an existing column's properties.

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

        # Validate table and column exist
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)
            await validator.validate_column_exists(table_id, column_id)

        try:
            updates = {}
            if label is not None:
                updates["label"] = label
            if col_type is not None:
                updates["type"] = col_type
            if formula is not None:
                updates["formula"] = formula
            if widget_options is not None:
                updates["widgetOptions"] = widget_options

            if not updates:
                from app.middleware.exceptions import ValidationException
                raise ValidationException("updates", "At least one property must be updated")

            await self.client.update_column(table_id, column_id, **updates)
            logger.debug(f"Updated column '{column_id}' in table '{table_id}'")

            return {"table_id": table_id, "column_id": column_id, "updated": True}

        except Exception as e:
            logger.error(f"Error updating column '{column_id}': {e}")
            raise

    async def remove_table_column(self, table_id: str, column_id: str) -> Dict[str, Any]:
        """
        Remove a column from a table.

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

        # Validate table and column exist
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)
            await validator.validate_column_exists(table_id, column_id)

        try:
            await self.client.delete_column(table_id, column_id)
            logger.debug(f"Removed column '{column_id}' from table '{table_id}'")

            return {"table_id": table_id, "column_id": column_id, "deleted": True}

        except Exception as e:
            logger.error(f"Error removing column '{column_id}': {e}")
            raise

    # ========================================================================
    # Page Operations
    # ========================================================================

    async def get_pages(self) -> List[Dict[str, Any]]:
        """
        Get all pages in the document.

        Returns:
            List of page objects with their IDs and metadata.
        """
        logger.info("Getting all pages")
        pages = await self.client.get_pages()
        logger.debug(f"Found {len(pages)} page(s)")
        return pages

    async def update_page(
        self, page_id: int, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a page's properties.

        Args:
            page_id: Page ID to update
            name: New name for the page (optional)

        Returns:
            Result confirming the update

        Raises:
            ValidationException: If updates are invalid
        """
        logger.info(f"Updating page {page_id}")

        updates = {}
        if name is not None:
            if not name or not name.strip():
                from app.middleware.exceptions import ValidationException
                raise ValidationException("name", "Page name cannot be empty")
            updates["name"] = name

        if not updates:
            from app.middleware.exceptions import ValidationException
            raise ValidationException("updates", "At least one property must be updated")

        try:
            await self.client.update_page(page_id, **updates)
            logger.debug(f"Updated page {page_id}")
            return {"page_id": page_id, "updated": True}

        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}")
            raise

    async def remove_page(self, page_id: int) -> Dict[str, Any]:
        """
        Remove a page from the document.

        WARNING: This is a destructive operation and cannot be undone.

        Args:
            page_id: Page ID to remove

        Returns:
            Result confirming the deletion
        """
        logger.warning(f"Removing page {page_id}")

        try:
            await self.client.delete_page(page_id)
            logger.debug(f"Removed page {page_id}")
            return {"page_id": page_id, "deleted": True}

        except Exception as e:
            logger.error(f"Error removing page {page_id}: {e}")
            raise

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def query_document(
        self, query: str, args: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query against the document.

        Args:
            query: SQL SELECT query
            args: Optional query arguments

        Returns:
            List of matching records.
        """
        logger.info(f"Executing query: {query[:100]}...")

        try:
            results = await self.client.query_sql(query, args)
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

        # Validate if enabled
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)
            for record in records:
                await validator.validate_record_data(table_id, record)

        try:
            # Format records for Grist API
            # Grist expects {"fields": {...}} for each record
            formatted_records = []
            for record in records:
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
            from app.middleware.exceptions import ValidationException

            raise ValidationException(
                "record_ids",
                f"Mismatch: {len(record_ids)} IDs but {len(records)} record objects",
            )

        # Validate if enabled
        validator = self._get_validator()
        if validator:
            await validator.validate_table_exists(table_id)
            for record in records:
                await validator.validate_record_data(table_id, record)

        try:
            # Format records for Grist API
            # Grist expects {"id": ..., "fields": {...}} for each record
            formatted_records = []
            for record_id, fields in zip(record_ids, records):
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


# TODO: Implement page and widget management operations
# - get_pages, update_page, remove_page
# - get_page_widgets, add_page_widget, update_page_widget, remove_page_widget
# - get_page_widget_select_by_options, set_page_widget_select_by
# - get_available_custom_widgets

# TODO: Add transaction support
# - Group multiple operations
# - Implement rollback on failure
# - Add dry-run mode

# TODO: Add caching
# - Cache table schemas (in ValidationService)
# - Cache frequently accessed data
# - Implement cache invalidation on writes
