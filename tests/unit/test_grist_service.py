"""
Unit Tests for GristService

Tests for high-level Grist service operations.
"""

import pytest
from unittest.mock import AsyncMock

from app.services.grist_service import GristService
from app.models import (
    TableNotFoundException,
    ColumnNotFoundException,
    ValidationException,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestGristService:
    """Tests for GristService."""

    async def test_get_tables(self, mock_grist_service, sample_tables):
        """Test getting all tables."""
        tables = await mock_grist_service.get_tables()
        assert len(tables) == 3
        assert tables[0]["id"] == "Students"
        assert tables[1]["id"] == "Projects"

    async def test_get_table_columns(self, mock_grist_service, sample_columns):
        """Test getting columns for a table."""
        columns = await mock_grist_service.get_table_columns("Students")
        assert len(columns) == 5
        assert columns[0]["id"] == "id"
        assert columns[1]["id"] == "Name"

    async def test_get_sample_records(self, mock_grist_service, sample_records):
        """Test getting sample records."""
        records = await mock_grist_service.get_sample_records("Students", limit=2)
        assert len(records) <= 10  # Max limit enforced
        assert len(records) > 0

    async def test_query_document(self, mock_grist_service):
        """Test SQL query execution."""
        results = await mock_grist_service.query_document(
            "SELECT * FROM Students WHERE Age > 18"
        )
        assert isinstance(results, list)

    async def test_add_records(self, mock_grist_service):
        """Test adding records."""
        new_records = [
            {"Name": "Alice", "Email": "alice@example.com", "Age": 22},
            {"Name": "Charlie", "Email": "charlie@example.com", "Age": 23},
        ]
        result = await mock_grist_service.add_records("Students", new_records)
        assert "record_ids" in result
        assert result["count"] == 2

    async def test_update_records(self, mock_grist_service):
        """Test updating records."""
        result = await mock_grist_service.update_records(
            "Students",
            record_ids=[1, 2],
            records=[
                {"Name": "John Updated"},
                {"Name": "Jane Updated"},
            ],
        )
        assert "updated_count" in result
        assert result["updated_count"] == 2

    async def test_update_records_mismatch(self, mock_grist_service):
        """Test update with mismatched IDs and records."""
        with pytest.raises(ValidationException) as exc_info:
            await mock_grist_service.update_records(
                "Students",
                record_ids=[1, 2, 3],
                records=[{"Name": "John"}],  # Only 1 record for 3 IDs
            )
        assert "Mismatch" in str(exc_info.value)

    async def test_remove_records(self, mock_grist_service):
        """Test removing records."""
        result = await mock_grist_service.remove_records("Students", [1, 2])
        assert "deleted_count" in result
        assert result["deleted_count"] == 2

    async def test_add_table(self, mock_grist_service):
        """Test creating a new table."""
        columns = [
            {"id": "Name", "fields": {"type": "Text"}},
            {"id": "Age", "fields": {"type": "Int"}},
        ]
        result = await mock_grist_service.add_table("NewTable", columns)
        assert "table_id" in result
        assert result["table_id"] == "NewTable"

    async def test_add_table_empty_id(self, mock_grist_service):
        """Test adding table with empty ID."""
        with pytest.raises(ValidationException) as exc_info:
            await mock_grist_service.add_table("", [])
        assert "Table ID cannot be empty" in str(exc_info.value)

    async def test_add_table_column(self, mock_grist_service):
        """Test adding a column to a table."""
        result = await mock_grist_service.add_table_column(
            "Students", "PhoneNumber", "Text", label="Phone"
        )
        assert "column_id" in result
        assert result["column_id"] == "PhoneNumber"

    async def test_update_table_column(self, mock_grist_service):
        """Test updating a column."""
        result = await mock_grist_service.update_table_column(
            "Students", "Name", label="Full Name"
        )
        assert result["updated"] is True

    async def test_remove_table_column(self, mock_grist_service):
        """Test removing a column."""
        result = await mock_grist_service.remove_table_column("Students", "Age")
        assert result["deleted"] is True

    async def test_service_cleanup(self, mock_grist_client):
        """Test service cleanup."""
        service = GristService(
            document_id="test",
            access_token="token",
            enable_validation=False,
        )
        service.client = mock_grist_client

        await service.close()
        mock_grist_client.close.assert_called_once()

    async def test_context_manager(self, mock_grist_client):
        """Test service as async context manager."""
        async with GristService(
            document_id="test",
            access_token="token",
            enable_validation=False,
        ) as service:
            service.client = mock_grist_client
            tables = await service.get_tables()
            assert len(tables) > 0

        # Verify cleanup was called
        mock_grist_client.close.assert_called()


@pytest.mark.unit
class TestGristServiceValidation:
    """Tests for GristService with validation enabled."""

    @pytest.mark.asyncio
    async def test_validation_enabled(self, mock_grist_client, sample_tables):
        """Test that validation service is created when enabled."""
        service = GristService(
            document_id="test",
            access_token="token",
            enable_validation=True,
        )
        service.client = mock_grist_client

        validator = service._get_validator()
        assert validator is not None

        await service.close()

    @pytest.mark.asyncio
    async def test_validation_disabled(self, mock_grist_client):
        """Test that validation is skipped when disabled."""
        service = GristService(
            document_id="test",
            access_token="token",
            enable_validation=False,
        )
        service.client = mock_grist_client

        # Should not raise even with invalid table
        await service.add_records("NonExistentTable", [{"foo": "bar"}])

        await service.close()
