"""
Unit Tests for Confirmation Service

Tests for confirmation workflow management.
"""

import pytest
from datetime import datetime, timedelta

from app.services.confirmation_service import (
    ConfirmationService,
    get_confirmation_service,
    requires_confirmation,
)
from app.models import OperationType, OperationPreview


@pytest.mark.unit
class TestConfirmationService:
    """Tests for ConfirmationService."""

    @pytest.fixture
    def service(self):
        """Create a fresh confirmation service for each test."""
        service = ConfirmationService()
        yield service
        service.clear_all()

    def test_create_confirmation(self, service):
        """Test creating a confirmation request."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Delete 5 records",
            affected_count=5,
            warnings=["Irreversible operation"],
            is_reversible=False,
        )

        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={"table_id": "Students", "record_ids": [1, 2, 3, 4, 5]},
            preview=preview,
        )

        assert confirmation.confirmation_id.startswith("conf_")
        assert confirmation.tool_name == "remove_records"
        assert confirmation.preview.affected_count == 5
        assert service.get_pending_count() == 1

    def test_get_confirmation_valid(self, service):
        """Test retrieving a valid confirmation."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Test",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        created = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={},
            preview=preview,
        )

        retrieved = service.get_confirmation(created.confirmation_id)
        assert retrieved is not None
        assert retrieved.confirmation_id == created.confirmation_id

    def test_get_confirmation_not_found(self, service):
        """Test retrieving non-existent confirmation."""
        result = service.get_confirmation("conf_doesnotexist")
        assert result is None

    def test_approve_confirmation(self, service):
        """Test approving a confirmation."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Test",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        created = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={"test": "value"},
            preview=preview,
        )

        # Approve
        approved = service.approve_confirmation(created.confirmation_id)
        assert approved is not None
        assert approved.confirmation_id == created.confirmation_id

        # Should be removed from pending after approval
        assert service.get_pending_count() == 0

        # Cannot approve twice
        second_attempt = service.approve_confirmation(created.confirmation_id)
        assert second_attempt is None

    def test_reject_confirmation(self, service):
        """Test rejecting a confirmation."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Test",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        created = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={},
            preview=preview,
        )

        # Reject
        result = service.reject_confirmation(created.confirmation_id)
        assert result is True

        # Should be removed from pending
        assert service.get_pending_count() == 0

    def test_confirmation_expiration(self, service):
        """Test that confirmations expire."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Test",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        # Create with very short expiration
        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={},
            preview=preview,
            expires_in_seconds=0,  # Expire immediately
        )

        # Should be expired when retrieved
        retrieved = service.get_confirmation(confirmation.confirmation_id)
        assert retrieved is None

        # Should be cleaned up
        assert service.get_pending_count() == 0

    def test_cleanup_expired(self, service):
        """Test cleanup of expired confirmations."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Test",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        # Create some confirmations with different expirations
        service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={},
            preview=preview,
            expires_in_seconds=0,  # Expired
        )

        service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={},
            preview=preview,
            expires_in_seconds=300,  # Valid
        )

        # Cleanup
        cleaned = service.cleanup_expired()
        assert cleaned == 1
        assert service.get_pending_count() == 1

    def test_multiple_confirmations(self, service):
        """Test managing multiple confirmations."""
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Test",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        conf1 = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={"id": 1},
            preview=preview,
        )

        conf2 = service.create_confirmation(
            operation_type=OperationType.DELETE_COLUMN,
            tool_name="remove_table_column",
            tool_args={"id": 2},
            preview=preview,
        )

        assert service.get_pending_count() == 2

        # Approve one
        service.approve_confirmation(conf1.confirmation_id)
        assert service.get_pending_count() == 1

        # Reject the other
        service.reject_confirmation(conf2.confirmation_id)
        assert service.get_pending_count() == 0


@pytest.mark.unit
class TestRequiresConfirmation:
    """Tests for requires_confirmation helper."""

    def test_remove_records_requires_confirmation(self):
        """Test that remove_records always requires confirmation."""
        assert requires_confirmation("remove_records", {}) is True

    def test_remove_column_requires_confirmation(self):
        """Test that remove_table_column always requires confirmation."""
        assert requires_confirmation("remove_table_column", {}) is True

    def test_update_records_bulk_requires_confirmation(self):
        """Test that bulk updates (>5 records) require confirmation."""
        # Small update - no confirmation
        assert (
            requires_confirmation(
                "update_records", {"record_ids": [1, 2, 3]}
            )
            is False
        )

        # Large update - requires confirmation
        assert (
            requires_confirmation(
                "update_records", {"record_ids": [1, 2, 3, 4, 5, 6, 7]}
            )
            is True
        )

    def test_update_column_type_requires_confirmation(self):
        """Test that column type changes require confirmation."""
        # No type change - no confirmation
        assert (
            requires_confirmation(
                "update_table_column", {"label": "New Label"}
            )
            is False
        )

        # Type change - requires confirmation
        assert (
            requires_confirmation(
                "update_table_column", {"col_type": "Int"}
            )
            is True
        )

    def test_safe_operations_no_confirmation(self):
        """Test that safe operations don't require confirmation."""
        assert requires_confirmation("get_tables", {}) is False
        assert requires_confirmation("get_table_columns", {}) is False
        assert requires_confirmation("query_document", {}) is False
        assert requires_confirmation("add_records", {}) is False


@pytest.mark.unit
def test_get_confirmation_service_singleton():
    """Test that get_confirmation_service returns singleton."""
    service1 = get_confirmation_service()
    service2 = get_confirmation_service()
    assert service1 is service2
