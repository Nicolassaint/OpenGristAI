"""
Unit Tests for Validation Service

Tests for data validation logic.
"""

import pytest
from unittest.mock import AsyncMock

from app.services.validation_service import ValidationService
from app.services.grist_service import GristService
from app.models import (
    TableNotFoundException,
    ColumnNotFoundException,
    TypeMismatchException,
    ChoiceValidationException,
    ValidationException,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidationService:
    """Tests for ValidationService."""

    @pytest.fixture
    def validation_service(self, mock_grist_service):
        """Create a validation service with mocked data."""
        validator = ValidationService(mock_grist_service)
        return validator

    async def test_validate_table_exists_valid(self, validation_service, sample_tables):
        """Test validation passes for existing table."""
        # Should not raise
        await validation_service.validate_table_exists("Students")

    async def test_validate_table_exists_invalid(self, validation_service):
        """Test validation fails for non-existent table."""
        with pytest.raises(TableNotFoundException) as exc_info:
            await validation_service.validate_table_exists("NonExistentTable")

        assert "NonExistentTable" in str(exc_info.value)
        assert "Available tables" in str(exc_info.value)

    async def test_validate_column_exists_valid(self, validation_service):
        """Test validation passes for existing column."""
        column = await validation_service.validate_column_exists("Students", "Name")
        assert column["id"] == "Name"

    async def test_validate_column_exists_invalid(self, validation_service):
        """Test validation fails for non-existent column."""
        with pytest.raises(ColumnNotFoundException) as exc_info:
            await validation_service.validate_column_exists(
                "Students", "NonExistentColumn"
            )

        assert "NonExistentColumn" in str(exc_info.value)
        assert "Available columns" in str(exc_info.value)

    async def test_validate_record_data_valid(self, validation_service):
        """Test validation passes for valid record data."""
        record = {
            "Name": "John Doe",
            "Email": "john@example.com",
            "Age": 20,
            "Grade": "A",
        }
        # Should not raise
        await validation_service.validate_record_data("Students", record)

    async def test_validate_field_type_text_valid(self, validation_service):
        """Test text field validation passes."""
        column = {"id": "Name", "type": "Text"}
        await validation_service._validate_field_type("Name", "John Doe", column)

    async def test_validate_field_type_text_invalid(self, validation_service):
        """Test text field validation fails for non-string."""
        column = {"id": "Name", "type": "Text"}
        with pytest.raises(TypeMismatchException) as exc_info:
            await validation_service._validate_field_type("Name", 123, column)

        assert "Expected type 'Text'" in str(exc_info.value)

    async def test_validate_field_type_int_valid(self, validation_service):
        """Test integer field validation passes."""
        column = {"id": "Age", "type": "Int"}
        await validation_service._validate_field_type("Age", 20, column)

    async def test_validate_field_type_int_invalid(self, validation_service):
        """Test integer field validation fails for non-integer."""
        column = {"id": "Age", "type": "Int"}
        with pytest.raises(TypeMismatchException) as exc_info:
            await validation_service._validate_field_type("Age", "twenty", column)

        assert "Expected type 'Int'" in str(exc_info.value)

    async def test_validate_field_type_numeric_valid(self, validation_service):
        """Test numeric field validation passes."""
        column = {"id": "Score", "type": "Numeric"}
        await validation_service._validate_field_type("Score", 95.5, column)
        await validation_service._validate_field_type("Score", 95, column)

    async def test_validate_field_type_bool_valid(self, validation_service):
        """Test boolean field validation passes."""
        column = {"id": "Active", "type": "Bool"}
        await validation_service._validate_field_type("Active", True, column)
        await validation_service._validate_field_type("Active", False, column)

    async def test_validate_field_type_choice_valid(self, validation_service):
        """Test choice field validation passes for valid choice."""
        column = {
            "id": "Grade",
            "type": "Choice",
            "widgetOptions": {"choices": ["A", "B", "C"]},
        }
        await validation_service._validate_field_type("Grade", "A", column)

    async def test_validate_field_type_choice_invalid(self, validation_service):
        """Test choice field validation fails for invalid choice."""
        column = {
            "id": "Grade",
            "type": "Choice",
            "widgetOptions": {"choices": ["A", "B", "C"]},
        }
        with pytest.raises(ChoiceValidationException) as exc_info:
            await validation_service._validate_field_type("Grade", "D", column)

        assert "not in allowed choices" in str(exc_info.value)

    async def test_validate_field_type_choice_list_valid(self, validation_service):
        """Test choice list field validation passes."""
        column = {
            "id": "Tags",
            "type": "ChoiceList",
            "widgetOptions": {"choices": ["Python", "JavaScript", "Go"]},
        }
        await validation_service._validate_field_type(
            "Tags", ["L", "Python", "Go"], column
        )

    async def test_validate_field_type_choice_list_invalid_format(
        self, validation_service
    ):
        """Test choice list validation fails without 'L' prefix."""
        column = {"id": "Tags", "type": "ChoiceList"}
        with pytest.raises(ValidationException) as exc_info:
            await validation_service._validate_field_type(
                "Tags", ["Python", "Go"], column
            )

        assert "must start with 'L'" in str(exc_info.value)

    async def test_validate_field_type_ref_valid(self, validation_service):
        """Test reference field validation passes for integer."""
        column = {"id": "StudentId", "type": "Ref"}
        await validation_service._validate_field_type("StudentId", 1, column)

    async def test_validate_field_type_ref_invalid(self, validation_service):
        """Test reference field validation fails for non-integer."""
        column = {"id": "StudentId", "type": "Ref"}
        with pytest.raises(TypeMismatchException) as exc_info:
            await validation_service._validate_field_type("StudentId", "abc", column)

        assert "record ID (integer)" in str(exc_info.value)

    async def test_validate_field_type_ref_list_valid(self, validation_service):
        """Test reference list field validation passes."""
        column = {"id": "RelatedIds", "type": "RefList"}
        await validation_service._validate_field_type(
            "RelatedIds", ["L", 1, 2, 3], column
        )

    async def test_validate_field_type_null_allowed(self, validation_service):
        """Test that null values are allowed for most fields."""
        column = {"id": "Name", "type": "Text"}
        # Should not raise
        await validation_service._validate_field_type("Name", None, column)

    async def test_cache_management(self, validation_service):
        """Test cache clearing."""
        # Load cache
        await validation_service.validate_table_exists("Students")
        assert validation_service._tables_cache is not None

        # Clear cache
        validation_service.clear_cache()
        assert validation_service._tables_cache is None
        assert len(validation_service._columns_cache) == 0
