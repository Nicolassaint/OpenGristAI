"""
Confirmation System

Handles confirmation workflow for destructive operations in the agent.
Combines confirmation service and handler logic.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.models import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationStatus,
    OperationPreview,
    OperationType,
)
from app.services.preview_service import PreviewService
from app.services.grist_service import GristService

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


class ConfirmationHandler:
    """Handles confirmation workflow in agent execution."""

    def __init__(self, grist_service: GristService, enabled: bool = True):
        """
        Initialize confirmation handler.

        Args:
            grist_service: GristService for preview generation
            enabled: Whether confirmations are enabled (default: True)
        """
        self.grist_service = grist_service
        self.enabled = enabled
        self.preview_service = PreviewService(grist_service)
        self.confirmation_service = ConfirmationService()

    def should_confirm(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """
        Check if a tool call requires confirmation.

        Args:
            tool_name: Name of the tool
            tool_args: Arguments for the tool

        Returns:
            True if confirmation required and enabled, False otherwise
        """
        if not self.enabled:
            return False

        return requires_confirmation(tool_name, tool_args)

    async def create_confirmation_request(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        document_id: str,
    ) -> ConfirmationRequest:
        """
        Create a confirmation request for a tool call.

        Args:
            tool_name: Name of the tool
            tool_args: Arguments for the tool
            document_id: Document ID (for context)

        Returns:
            ConfirmationRequest

        Raises:
            ValueError: If preview generation fails
        """
        logger.info(f"Creating confirmation request for {tool_name}")

        # Generate preview based on operation type
        preview = await self._generate_preview(tool_name, tool_args)

        # Add document_id to tool_args for later execution
        tool_args_with_doc = {**tool_args, "document_id": document_id}

        # Determine operation type
        operation_type = self._get_operation_type(tool_name)

        # Create confirmation request
        confirmation = self.confirmation_service.create_confirmation(
            operation_type=operation_type,
            tool_name=tool_name,
            tool_args=tool_args_with_doc,
            preview=preview,
            expires_in_seconds=300,  # 5 minutes
        )

        logger.info(
            f"Created confirmation {confirmation.confirmation_id} for {tool_name}"
        )

        return confirmation

    async def _generate_preview(
        self, tool_name: str, tool_args: Dict[str, Any]
    ) -> OperationPreview:
        """
        Generate preview for a tool operation.

        Args:
            tool_name: Name of the tool
            tool_args: Arguments for the tool

        Returns:
            OperationPreview

        Raises:
            ValueError: If tool not supported for preview
        """
        if tool_name == "remove_records":
            return await self.preview_service.preview_remove_records(
                table_id=tool_args["table_id"],
                record_ids=tool_args["record_ids"],
            )

        elif tool_name == "remove_table_column":
            return await self.preview_service.preview_remove_column(
                table_id=tool_args["table_id"],
                column_id=tool_args["column_id"],
            )

        elif tool_name == "update_records":
            return await self.preview_service.preview_update_records(
                table_id=tool_args["table_id"],
                record_ids=tool_args["record_ids"],
                records=tool_args["records"],
            )

        elif tool_name == "update_table_column":
            # Need to fetch current type first
            columns = await self.grist_service.get_table_columns(tool_args["table_id"])
            column = next(
                (c for c in columns if c["id"] == tool_args["column_id"]), None
            )

            if column:
                old_type = column.get("fields", {}).get("type", "Unknown")
                new_type = tool_args.get("col_type", old_type)

                return await self.preview_service.preview_update_column_type(
                    table_id=tool_args["table_id"],
                    column_id=tool_args["column_id"],
                    old_type=old_type,
                    new_type=new_type,
                )
            else:
                # Column not found, create simple preview
                return OperationPreview(
                    operation_type=OperationType.UPDATE_COLUMN_TYPE,
                    description=f"Update column {tool_args['column_id']}",
                    affected_count=1,
                    warnings=["Column type will be changed"],
                    is_reversible=False,
                )

        else:
            raise ValueError(f"Preview not supported for tool: {tool_name}")

    def _get_operation_type(self, tool_name: str) -> OperationType:
        """
        Get operation type from tool name.

        Args:
            tool_name: Name of the tool

        Returns:
            OperationType
        """
        operation_map = {
            "remove_records": OperationType.DELETE_RECORDS,
            "remove_table_column": OperationType.DELETE_COLUMN,
            "update_records": OperationType.UPDATE_RECORDS,
            "update_table_column": OperationType.UPDATE_COLUMN_TYPE,
        }

        return operation_map.get(tool_name, OperationType.UPDATE_RECORDS)


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
