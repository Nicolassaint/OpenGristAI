"""
Integration tests for case-insensitive operations in GristService.

Tests the full workflow of case-insensitive table/column matching.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.grist_service import GristService
from app.services.grist_client import GristAPIClient


@pytest.fixture
def mock_grist_client():
    """Create a mock GristAPIClient."""
    client = MagicMock(spec=GristAPIClient)

    # Mock get_tables
    client.get_tables = AsyncMock(return_value=[
        {"id": "Clients", "fields": {}},
        {"id": "Products", "fields": {}},
    ])

    # Mock get_table_columns
    client.get_table_columns = AsyncMock(return_value=[
        {
            "id": "Nom",
            "fields": {
                "type": "Text",
                "label": "Nom",
                "colRef": 1,
            }
        },
        {
            "id": "Email",
            "fields": {
                "type": "Text",
                "label": "Email",
                "colRef": 2,
            }
        },
    ])

    # Mock CRUD operations
    client.add_column = AsyncMock(return_value={"id": "TestColumn"})
    client.update_column = AsyncMock()
    client.delete_column = AsyncMock()
    client.get_records = AsyncMock(return_value=[])
    client.add_records = AsyncMock(return_value={"records": [{"id": 1}, {"id": 2}, {"id": 3}]})
    client.update_records = AsyncMock()

    return client


@pytest.fixture
def grist_service(mock_grist_client):
    """Create a GristService with mocked client."""
    service = GristService(
        document_id="test-doc",
        access_token="test-token",
        base_url="https://test.getgrist.com"
    )
    service.client = mock_grist_client
    return service


@pytest.mark.integration
@pytest.mark.asyncio
class TestAddTableColumnCaseInsensitive:
    """Test add_table_column with case-insensitive table names."""

    async def test_lowercase_table_name(self, grist_service, mock_grist_client):
        """Test adding column to lowercase table name."""
        result = await grist_service.add_table_column(
            table_id="clients",  # lowercase
            column_id="Phone",
            col_type="Text"
        )

        # Should call with corrected table name
        mock_grist_client.add_column.assert_called_once()
        call_args = mock_grist_client.add_column.call_args
        assert call_args[0][0] == "Clients"  # Corrected to proper case

    async def test_uppercase_table_name(self, grist_service, mock_grist_client):
        """Test adding column to uppercase table name."""
        result = await grist_service.add_table_column(
            table_id="CLIENTS",  # uppercase
            column_id="Phone",
            col_type="Text"
        )

        # Should call with corrected table name
        call_args = mock_grist_client.add_column.call_args
        assert call_args[0][0] == "Clients"


@pytest.mark.integration
@pytest.mark.asyncio
class TestUpdateTableColumnCaseInsensitive:
    """Test update_table_column with case-insensitive names."""

    async def test_lowercase_table_and_column(self, grist_service, mock_grist_client):
        """Test updating with lowercase table and column names."""
        result = await grist_service.update_table_column(
            table_id="clients",  # lowercase
            column_id="nom",     # lowercase
            label="Full Name"
        )

        # Should call with corrected names
        call_args = mock_grist_client.update_column.call_args
        assert call_args[0][0] == "Clients"  # Table corrected
        assert call_args[0][1] == "Nom"      # Column corrected

    async def test_mixed_case_names(self, grist_service, mock_grist_client):
        """Test updating with mixed case names."""
        result = await grist_service.update_table_column(
            table_id="cLiEnTs",
            column_id="eMAIL",
            label="Email Address"
        )

        call_args = mock_grist_client.update_column.call_args
        assert call_args[0][0] == "Clients"
        assert call_args[0][1] == "Email"


@pytest.mark.integration
@pytest.mark.asyncio
class TestRemoveTableColumnCaseInsensitive:
    """Test remove_table_column with case-insensitive names."""

    async def test_lowercase_column_removal(self, grist_service, mock_grist_client):
        """Test removing column with lowercase name."""
        result = await grist_service.remove_table_column(
            table_id="clients",
            column_id="nom"
        )

        # Should call with corrected names
        call_args = mock_grist_client.delete_column.call_args
        assert call_args[0][0] == "Clients"
        assert call_args[0][1] == "Nom"

    async def test_uppercase_column_removal(self, grist_service, mock_grist_client):
        """Test removing column with uppercase name."""
        result = await grist_service.remove_table_column(
            table_id="CLIENTS",
            column_id="EMAIL"
        )

        call_args = mock_grist_client.delete_column.call_args
        assert call_args[0][0] == "Clients"
        assert call_args[0][1] == "Email"


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetSampleRecordsCaseInsensitive:
    """Test get_sample_records with case-insensitive table names."""

    async def test_lowercase_table_name(self, grist_service, mock_grist_client):
        """Test getting samples from lowercase table name."""
        result = await grist_service.get_sample_records(
            table_id="clients",
            limit=5
        )

        # Should call with corrected table name
        mock_grist_client.get_records.assert_called_once()
        call_args = mock_grist_client.get_records.call_args
        assert call_args[0][0] == "Clients"


@pytest.mark.integration
@pytest.mark.asyncio
class TestAddRecordsCaseInsensitive:
    """Test add_records with case-insensitive field names."""

    async def test_lowercase_field_names(self, grist_service, mock_grist_client):
        """Test adding records with lowercase field names."""
        records = [
            {"nom": "Jean", "email": "jean@example.com"},
            {"nom": "Marie", "email": "marie@example.com"},
        ]

        result = await grist_service.add_records("clients", records)

        # Should call with corrected table and field names
        mock_grist_client.add_records.assert_called_once()
        call_args = mock_grist_client.add_records.call_args

        # Check table name corrected
        assert call_args[0][0] == "Clients"

        # Check field names corrected in records
        formatted_records = call_args[0][1]
        assert formatted_records[0]["fields"] == {"Nom": "Jean", "Email": "jean@example.com"}
        assert formatted_records[1]["fields"] == {"Nom": "Marie", "Email": "marie@example.com"}

    async def test_mixed_case_field_names(self, grist_service, mock_grist_client):
        """Test adding records with mixed case field names."""
        records = [
            {"NOM": "Jean", "email": "jean@example.com"},
        ]

        result = await grist_service.add_records("CLIENTS", records)

        call_args = mock_grist_client.add_records.call_args
        formatted_records = call_args[0][1]

        # Both should be corrected to proper case
        assert formatted_records[0]["fields"] == {"Nom": "Jean", "Email": "jean@example.com"}

    async def test_exact_match_not_modified(self, grist_service, mock_grist_client):
        """Test that exact match field names are not modified."""
        records = [
            {"Nom": "Jean", "Email": "jean@example.com"},
        ]

        result = await grist_service.add_records("Clients", records)

        call_args = mock_grist_client.add_records.call_args
        formatted_records = call_args[0][1]

        # Should remain unchanged
        assert formatted_records[0]["fields"] == {"Nom": "Jean", "Email": "jean@example.com"}


@pytest.mark.integration
@pytest.mark.asyncio
class TestUpdateRecordsCaseInsensitive:
    """Test update_records with case-insensitive field names."""

    async def test_lowercase_field_names_update(self, grist_service, mock_grist_client):
        """Test updating records with lowercase field names."""
        record_ids = [1, 2]
        records = [
            {"nom": "Jean Updated"},
            {"email": "new@example.com"},
        ]

        result = await grist_service.update_records("clients", record_ids, records)

        # Should call with corrected names
        call_args = mock_grist_client.update_records.call_args

        assert call_args[0][0] == "Clients"

        formatted_records = call_args[0][1]
        assert formatted_records[0]["fields"] == {"Nom": "Jean Updated"}
        assert formatted_records[1]["fields"] == {"Email": "new@example.com"}

    async def test_update_with_id_field(self, grist_service, mock_grist_client):
        """Test that 'id' field in update is preserved."""
        record_ids = [1]
        records = [
            {"id": 999, "nom": "Jean"},  # id should be preserved
        ]

        result = await grist_service.update_records("Clients", record_ids, records)

        call_args = mock_grist_client.update_records.call_args
        formatted_records = call_args[0][1]

        # ID from record_ids should be used, not from fields
        assert formatted_records[0]["id"] == 1
        assert formatted_records[0]["fields"] == {"id": 999, "Nom": "Jean"}


@pytest.mark.integration
@pytest.mark.asyncio
class TestCaseInsensitiveRegression:
    """Regression tests to ensure no side effects."""

    async def test_exact_match_still_works(self, grist_service, mock_grist_client):
        """Test that exact matches still work after case-insensitive changes."""
        # This should work exactly as before
        result = await grist_service.add_records(
            "Clients",
            [{"Nom": "Jean", "Email": "jean@example.com"}]
        )

        call_args = mock_grist_client.add_records.call_args
        assert call_args[0][0] == "Clients"
        formatted_records = call_args[0][1]
        assert formatted_records[0]["fields"] == {"Nom": "Jean", "Email": "jean@example.com"}

    async def test_performance_no_degradation(self, grist_service, mock_grist_client):
        """Test that performance doesn't degrade with caching."""
        # Multiple operations should use cache
        await grist_service.add_records("Clients", [{"Nom": "Jean"}])
        await grist_service.add_records("Clients", [{"Email": "test@example.com"}])

        # Should only fetch tables once (cached)
        assert mock_grist_client.get_tables.call_count == 1

        # Should only fetch columns once (cached)
        assert mock_grist_client.get_table_columns.call_count == 1
