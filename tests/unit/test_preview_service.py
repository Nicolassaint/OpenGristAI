"""
Unit Tests for Preview Service

Tests for operation preview generation.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.preview_service import PreviewService
from app.models import OperationType


@pytest.mark.unit
@pytest.mark.asyncio
class TestPreviewService:
    """Tests for PreviewService."""

    @pytest.fixture
    def preview_service(self, mock_grist_service):
        """Create a preview service with mocked Grist service."""
        return PreviewService(mock_grist_service)

    async def test_preview_remove_records(self, preview_service, mock_grist_service):
        """Test preview for record deletion."""
        # Mock query to return sample records
        mock_grist_service.query_document = AsyncMock(return_value=[
            {"id": 1, "Name": "John", "Age": 20},
            {"id": 2, "Name": "Jane", "Age": 21},
        ])

        preview = await preview_service.preview_remove_records(
            table_id="Students", record_ids=[1, 2, 3, 4, 5]
        )

        assert preview.operation_type == OperationType.DELETE_RECORDS
        assert preview.affected_count == 5
        assert preview.is_reversible is False
        assert len(preview.warnings) > 0
        assert "IRRÉVERSIBLE" in preview.warnings[0]
        assert preview.description == "Supprimer 5 enregistrement(s) de la table 'Students'"

    async def test_preview_remove_column(self, preview_service, mock_grist_service):
        """Test preview for column deletion."""
        # Mock get_table_columns
        mock_grist_service.get_table_columns = AsyncMock(return_value=[
            {"id": "Name", "fields": {"type": "Text", "label": "Full Name"}},
            {"id": "Age", "fields": {"type": "Int", "label": "Age"}},
        ])

        # Mock query to count records with data
        mock_grist_service.query_document = AsyncMock(return_value=[{"count": 25}])

        preview = await preview_service.preview_remove_column(
            table_id="Students", column_id="Age"
        )

        assert preview.operation_type == OperationType.DELETE_COLUMN
        assert preview.affected_count == 25
        assert preview.is_reversible is False
        assert any("IRRÉVERSIBLE" in w for w in preview.warnings)
        assert any("25 enregistrement(s)" in w for w in preview.warnings)

    async def test_preview_update_records(self, preview_service, mock_grist_service):
        """Test preview for record updates."""
        # Mock query to return current records
        mock_grist_service.query_document = AsyncMock(return_value=[
            {"id": 1, "Name": "John", "Grade": "B"},
            {"id": 2, "Name": "Jane", "Grade": "C"},
        ])

        new_records = [
            {"Grade": "A"},
            {"Grade": "A"},
        ]

        preview = await preview_service.preview_update_records(
            table_id="Students", record_ids=[1, 2], records=new_records
        )

        assert preview.operation_type == OperationType.UPDATE_RECORDS
        assert preview.affected_count == 2
        assert len(preview.affected_items) == 2

        # Check before/after
        item = preview.affected_items[0]
        assert "before" in item
        assert "after" in item
        assert "changes" in item
        assert "Grade" in item["changes"]

    async def test_preview_update_records_bulk_warning(
        self, preview_service, mock_grist_service
    ):
        """Test that bulk updates show warning."""
        mock_grist_service.query_document = AsyncMock(return_value=[])

        # Create 15 records update
        record_ids = list(range(1, 16))
        records = [{"Grade": "A"} for _ in range(15)]

        preview = await preview_service.preview_update_records(
            table_id="Students", record_ids=record_ids, records=records
        )

        assert preview.affected_count == 15
        assert any("Modification massive" in w for w in preview.warnings)
        assert any("15 enregistrements" in w for w in preview.warnings)

    async def test_preview_update_column_type(self, preview_service):
        """Test preview for column type change."""
        preview = await preview_service.preview_update_column_type(
            table_id="Students",
            column_id="Age",
            old_type="Text",
            new_type="Int",
        )

        assert preview.operation_type == OperationType.UPDATE_COLUMN_TYPE
        assert preview.affected_count == 1
        assert preview.is_reversible is False
        assert any("Text" in w and "Int" in w for w in preview.warnings)

    async def test_preview_column_type_lossy_conversion(self, preview_service):
        """Test preview shows warning for lossy conversions."""
        preview = await preview_service.preview_update_column_type(
            table_id="Students",
            column_id="Score",
            old_type="Numeric",
            new_type="Int",
        )

        # Should warn about potential data loss (decimals truncated)
        assert any("PERTE DE DONNÉES" in w for w in preview.warnings)

    async def test_preview_remove_records_query_error(
        self, preview_service, mock_grist_service
    ):
        """Test preview handles query errors gracefully."""
        # Make query fail
        mock_grist_service.query_document = AsyncMock(side_effect=Exception("Query failed"))

        # Should not crash, just return empty affected_items
        preview = await preview_service.preview_remove_records(
            table_id="Students", record_ids=[1, 2, 3]
        )

        assert preview.affected_count == 3
        assert preview.affected_items == []
        assert len(preview.warnings) > 0

    async def test_preview_remove_column_count_error(
        self, preview_service, mock_grist_service
    ):
        """Test preview handles count query errors."""
        mock_grist_service.get_table_columns = AsyncMock(return_value=[
            {"id": "Age", "fields": {"type": "Int", "label": "Age"}},
        ])

        # Make count query fail
        mock_grist_service.query_document = AsyncMock(side_effect=Exception("Count failed"))

        preview = await preview_service.preview_remove_column(
            table_id="Students", column_id="Age"
        )

        # Should default to 0 records
        assert preview.affected_count == 0
        assert any("IRRÉVERSIBLE" in w for w in preview.warnings)
