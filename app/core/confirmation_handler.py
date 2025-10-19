"""
Confirmation Handler

Handles detection and creation of confirmation requests in the agent workflow.
"""

import logging
from typing import Any, Dict, Optional

from app.models import ConfirmationRequest, OperationPreview, OperationType
from app.services.confirmation_service import (
    get_confirmation_service,
    requires_confirmation,
)
from app.services.preview_service import PreviewService
from app.services.grist_service import GristService

logger = logging.getLogger(__name__)


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
        self.confirmation_service = get_confirmation_service()

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
            column = next((c for c in columns if c["id"] == tool_args["column_id"]), None)

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
