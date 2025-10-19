"""
Confirmation Service

Manages confirmation requests for destructive operations.
Stores pending confirmations and validates user decisions.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationStatus,
    OperationPreview,
    OperationType,
)

logger = logging.getLogger(__name__)


class ConfirmationService:
    """
    Service for managing operation confirmations.

    In-memory storage for now, can be replaced with Redis for production.
    """

    def __init__(self):
        """Initialize the confirmation service."""
        # Store pending confirmations: {confirmation_id: (request, created_at)}
        self._pending: Dict[str, tuple[ConfirmationRequest, datetime]] = {}

    def create_confirmation(
        self,
        operation_type: OperationType,
        tool_name: str,
        tool_args: Dict[str, Any],
        preview: OperationPreview,
        expires_in_seconds: int = 300,
    ) -> ConfirmationRequest:
        """
        Create a new confirmation request.

        Args:
            operation_type: Type of operation
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            preview: Preview of the operation
            expires_in_seconds: How long the confirmation is valid (default: 5 minutes)

        Returns:
            ConfirmationRequest object
        """
        confirmation_id = f"conf_{uuid.uuid4().hex[:12]}"

        request = ConfirmationRequest(
            confirmation_id=confirmation_id,
            preview=preview,
            tool_name=tool_name,
            tool_args=tool_args,
            expires_in_seconds=expires_in_seconds,
        )

        # Store in pending confirmations
        self._pending[confirmation_id] = (request, datetime.now())

        logger.info(
            f"Created confirmation request {confirmation_id} for {tool_name} "
            f"affecting {preview.affected_count} items"
        )

        return request

    def get_confirmation(self, confirmation_id: str) -> Optional[ConfirmationRequest]:
        """
        Get a pending confirmation request.

        Args:
            confirmation_id: ID of the confirmation

        Returns:
            ConfirmationRequest if found and not expired, None otherwise
        """
        if confirmation_id not in self._pending:
            logger.warning(f"Confirmation {confirmation_id} not found")
            return None

        request, created_at = self._pending[confirmation_id]

        # Check if expired
        expires_at = created_at + timedelta(seconds=request.expires_in_seconds)
        if datetime.now() > expires_at:
            logger.warning(f"Confirmation {confirmation_id} has expired")
            # Clean up expired confirmation
            del self._pending[confirmation_id]
            return None

        return request

    def approve_confirmation(
        self, confirmation_id: str
    ) -> Optional[ConfirmationRequest]:
        """
        Approve a confirmation and remove it from pending.

        Args:
            confirmation_id: ID of the confirmation

        Returns:
            ConfirmationRequest if found and valid, None otherwise
        """
        request = self.get_confirmation(confirmation_id)
        if request is None:
            return None

        # Remove from pending (can only be used once)
        del self._pending[confirmation_id]

        logger.info(f"Confirmation {confirmation_id} approved")
        return request

    def reject_confirmation(self, confirmation_id: str) -> bool:
        """
        Reject a confirmation and remove it from pending.

        Args:
            confirmation_id: ID of the confirmation

        Returns:
            True if confirmation was found and rejected, False otherwise
        """
        if confirmation_id not in self._pending:
            return False

        del self._pending[confirmation_id]
        logger.info(f"Confirmation {confirmation_id} rejected")
        return True

    def cleanup_expired(self) -> int:
        """
        Remove all expired confirmations.

        Returns:
            Number of confirmations cleaned up
        """
        now = datetime.now()
        expired_ids = []

        for conf_id, (request, created_at) in self._pending.items():
            expires_at = created_at + timedelta(seconds=request.expires_in_seconds)
            if now > expires_at:
                expired_ids.append(conf_id)

        for conf_id in expired_ids:
            del self._pending[conf_id]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired confirmations")

        return len(expired_ids)

    def get_pending_count(self) -> int:
        """Get the number of pending confirmations."""
        # Clean up expired first
        self.cleanup_expired()
        return len(self._pending)

    def clear_all(self) -> None:
        """Clear all pending confirmations (for testing)."""
        self._pending.clear()
        logger.info("Cleared all pending confirmations")


# Global confirmation service instance
_confirmation_service: Optional[ConfirmationService] = None


def get_confirmation_service() -> ConfirmationService:
    """
    Get the global confirmation service instance.

    Returns:
        ConfirmationService singleton
    """
    global _confirmation_service
    if _confirmation_service is None:
        _confirmation_service = ConfirmationService()
    return _confirmation_service


# Helper function to determine if an operation requires confirmation
def requires_confirmation(tool_name: str, tool_args: Dict[str, Any]) -> bool:
    """
    Determine if a tool operation requires user confirmation.

    Args:
        tool_name: Name of the tool
        tool_args: Arguments for the tool

    Returns:
        True if confirmation is required, False otherwise
    """
    # Always require confirmation for deletions
    if tool_name in ["remove_records", "remove_table_column"]:
        return True

    # Require confirmation for bulk updates (>5 records)
    if tool_name == "update_records":
        record_ids = tool_args.get("record_ids", [])
        if len(record_ids) > 5:
            return True

    # Require confirmation for column type changes
    if tool_name == "update_table_column":
        # Check if changing the type
        if "col_type" in tool_args:
            return True

    return False
