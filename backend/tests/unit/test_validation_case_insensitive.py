"""
Tests for case-insensitive validation in ValidationService.

Tests the fuzzy matching functionality for tables and columns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.validation_service import ValidationService
from app.models.exceptions import TableNotFoundException, ColumnNotFoundException


@pytest.fixture
def mock_grist_service():
    """Create a mock GristService with sample data."""
    service = MagicMock()

    # Mock get_tables
    service.get_tables = AsyncMock(return_value=[
        {"id": "Clients", "fields": {}},
        {"id": "Products", "fields": {}},
        {"id": "Orders", "fields": {}},
    ])

    # Mock get_table_columns for "Clients"
    service.get_table_columns = AsyncMock(return_value=[
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
        {
            "id": "Age",
            "fields": {
                "type": "Int",
                "label": "Age",
                "colRef": 3,
            }
        },
    ])

    return service


@pytest.mark.unit
@pytest.mark.asyncio
class TestTableValidationCaseInsensitive:
    """Test case-insensitive table validation."""

    async def test_exact_match_takes_priority(self, mock_grist_service):
        """Test that exact match is preferred over case-insensitive."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_table_exists("Clients")

        assert result == "Clients"

    async def test_lowercase_table_name(self, mock_grist_service):
        """Test finding table with lowercase name."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_table_exists("clients")

        assert result == "Clients"

    async def test_uppercase_table_name(self, mock_grist_service):
        """Test finding table with uppercase name."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_table_exists("CLIENTS")

        assert result == "Clients"

    async def test_mixed_case_table_name(self, mock_grist_service):
        """Test finding table with mixed case name."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_table_exists("cLiEnTs")

        assert result == "Clients"

    async def test_table_not_found(self, mock_grist_service):
        """Test that non-existent table raises exception."""
        validator = ValidationService(mock_grist_service)

        with pytest.raises(TableNotFoundException) as exc_info:
            await validator.validate_table_exists("NonExistent")

        assert "NonExistent" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
class TestColumnValidationCaseInsensitive:
    """Test case-insensitive column validation."""

    async def test_exact_match_column(self, mock_grist_service):
        """Test that exact match is preferred for columns."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_column_exists("Clients", "Nom")

        assert result["id"] == "Nom"
        assert result["fields"]["type"] == "Text"

    async def test_lowercase_column_name(self, mock_grist_service):
        """Test finding column with lowercase name."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_column_exists("Clients", "nom")

        assert result["id"] == "Nom"

    async def test_uppercase_column_name(self, mock_grist_service):
        """Test finding column with uppercase name."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_column_exists("Clients", "EMAIL")

        assert result["id"] == "Email"

    async def test_mixed_case_column_name(self, mock_grist_service):
        """Test finding column with mixed case name."""
        validator = ValidationService(mock_grist_service)

        result = await validator.validate_column_exists("Clients", "aGe")

        assert result["id"] == "Age"

    async def test_column_not_found(self, mock_grist_service):
        """Test that non-existent column raises exception."""
        validator = ValidationService(mock_grist_service)

        with pytest.raises(ColumnNotFoundException) as exc_info:
            await validator.validate_column_exists("Clients", "NonExistent")

        assert "NonExistent" in str(exc_info.value)

    async def test_case_insensitive_table_and_column(self, mock_grist_service):
        """Test case-insensitive matching for both table and column."""
        validator = ValidationService(mock_grist_service)

        # Both table and column in lowercase
        result = await validator.validate_column_exists("clients", "email")

        assert result["id"] == "Email"


@pytest.mark.unit
@pytest.mark.asyncio
class TestRecordDataValidationCaseInsensitive:
    """Test case-insensitive record data validation."""

    async def test_exact_match_record_fields(self, mock_grist_service):
        """Test that exact match fields are not modified."""
        validator = ValidationService(mock_grist_service)

        record = {"Nom": "Jean", "Email": "jean@example.com"}
        result = await validator.validate_record_data("Clients", record)

        assert result == {"Nom": "Jean", "Email": "jean@example.com"}

    async def test_lowercase_field_names_corrected(self, mock_grist_service):
        """Test that lowercase field names are corrected."""
        validator = ValidationService(mock_grist_service)

        record = {"nom": "Jean", "email": "jean@example.com"}
        result = await validator.validate_record_data("Clients", record)

        # Should correct to proper case
        assert result == {"Nom": "Jean", "Email": "jean@example.com"}

    async def test_uppercase_field_names_corrected(self, mock_grist_service):
        """Test that uppercase field names are corrected."""
        validator = ValidationService(mock_grist_service)

        record = {"NOM": "Jean", "EMAIL": "jean@example.com"}
        result = await validator.validate_record_data("Clients", record)

        assert result == {"Nom": "Jean", "Email": "jean@example.com"}

    async def test_mixed_case_fields(self, mock_grist_service):
        """Test record with mix of correct and incorrect case."""
        validator = ValidationService(mock_grist_service)

        record = {"Nom": "Jean", "email": "jean@example.com", "AGE": 30}
        result = await validator.validate_record_data("Clients", record)

        assert result == {"Nom": "Jean", "Email": "jean@example.com", "Age": 30}

    async def test_id_field_preserved(self, mock_grist_service):
        """Test that 'id' field is preserved without validation."""
        validator = ValidationService(mock_grist_service)

        record = {"id": 123, "nom": "Jean"}
        result = await validator.validate_record_data("Clients", record)

        assert result == {"id": 123, "Nom": "Jean"}

    async def test_invalid_field_raises_exception(self, mock_grist_service):
        """Test that invalid field name raises exception."""
        validator = ValidationService(mock_grist_service)

        record = {"NonExistent": "value"}

        with pytest.raises(ColumnNotFoundException):
            await validator.validate_record_data("Clients", record)


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidationCache:
    """Test that validation uses caching properly."""

    async def test_tables_cache_used(self, mock_grist_service):
        """Test that tables are cached after first call."""
        validator = ValidationService(mock_grist_service)

        # First call - should fetch
        await validator.validate_table_exists("Clients")
        assert mock_grist_service.get_tables.call_count == 1

        # Second call - should use cache
        await validator.validate_table_exists("products")
        assert mock_grist_service.get_tables.call_count == 1  # No additional call

    async def test_columns_cache_used(self, mock_grist_service):
        """Test that columns are cached after first call."""
        validator = ValidationService(mock_grist_service)

        # First call - should fetch
        await validator.validate_column_exists("Clients", "Nom")
        assert mock_grist_service.get_table_columns.call_count == 1

        # Second call - should use cache
        await validator.validate_column_exists("Clients", "email")
        assert mock_grist_service.get_table_columns.call_count == 1  # No additional call

    async def test_cache_can_be_cleared(self, mock_grist_service):
        """Test that cache can be manually cleared."""
        validator = ValidationService(mock_grist_service)

        # Populate cache
        await validator.validate_table_exists("Clients")
        assert mock_grist_service.get_tables.call_count == 1

        # Clear cache
        validator.clear_cache()

        # Should fetch again
        await validator.validate_table_exists("Clients")
        assert mock_grist_service.get_tables.call_count == 2
