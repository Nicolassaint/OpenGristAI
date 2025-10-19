"""
Preview Service

Generates previews of destructive operations before execution.
"""

import logging
from typing import Any, Dict, List

from app.models import OperationPreview, OperationType
from app.services.grist_service import GristService

logger = logging.getLogger(__name__)


class PreviewService:
    """Service for generating operation previews."""

    def __init__(self, grist_service: GristService):
        """
        Initialize the preview service.

        Args:
            grist_service: GristService instance for querying data
        """
        self.grist_service = grist_service

    async def preview_remove_records(
        self, table_id: str, record_ids: List[int]
    ) -> OperationPreview:
        """
        Generate preview for record deletion.

        Args:
            table_id: Table ID
            record_ids: List of record IDs to delete

        Returns:
            OperationPreview
        """
        affected_count = len(record_ids)

        # Fetch the records that will be deleted (limit to 10 for preview)
        preview_ids = record_ids[:10]
        query = f"SELECT * FROM {table_id} WHERE id IN ({','.join('?' * len(preview_ids))})"

        try:
            affected_items = await self.grist_service.query_document(query, preview_ids)
        except Exception as e:
            logger.warning(f"Could not fetch records for preview: {e}")
            affected_items = []

        warnings = [
            "⚠️ Cette opération est IRRÉVERSIBLE",
            f"⚠️ {affected_count} enregistrement(s) seront définitivement supprimés",
        ]

        # Check for potential references (simplified - could be enhanced)
        if affected_count > 10:
            warnings.append(
                f"⚠️ Suppression massive : {affected_count} enregistrements seront affectés"
            )

        return OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description=f"Supprimer {affected_count} enregistrement(s) de la table '{table_id}'",
            affected_count=affected_count,
            affected_items=affected_items[:10],  # Show max 10
            warnings=warnings,
            is_reversible=False,
        )

    async def preview_remove_column(
        self, table_id: str, column_id: str
    ) -> OperationPreview:
        """
        Generate preview for column deletion.

        Args:
            table_id: Table ID
            column_id: Column ID to delete

        Returns:
            OperationPreview
        """
        # Get column info
        try:
            columns = await self.grist_service.get_table_columns(table_id)
            column = next((c for c in columns if c["id"] == column_id), None)
            column_label = column.get("fields", {}).get("label", column_id) if column else column_id
        except Exception:
            column_label = column_id

        # Count how many records have data in this column
        try:
            query = f"SELECT COUNT(*) as count FROM {table_id} WHERE {column_id} IS NOT NULL"
            result = await self.grist_service.query_document(query)
            records_with_data = result[0].get("count", 0) if result else 0
        except Exception as e:
            logger.warning(f"Could not count records with data: {e}")
            records_with_data = 0

        warnings = [
            "⚠️ Cette opération est IRRÉVERSIBLE",
            f"⚠️ La colonne '{column_label}' et TOUTES ses données seront définitivement supprimées",
        ]

        if records_with_data > 0:
            warnings.append(
                f"⚠️ {records_with_data} enregistrement(s) contiennent des données dans cette colonne"
            )

        return OperationPreview(
            operation_type=OperationType.DELETE_COLUMN,
            description=f"Supprimer la colonne '{column_label}' de la table '{table_id}'",
            affected_count=records_with_data,
            affected_items=[
                {
                    "table": table_id,
                    "column": column_id,
                    "label": column_label,
                    "records_with_data": records_with_data,
                }
            ],
            warnings=warnings,
            is_reversible=False,
        )

    async def preview_update_records(
        self, table_id: str, record_ids: List[int], records: List[Dict[str, Any]]
    ) -> OperationPreview:
        """
        Generate preview for record updates.

        Args:
            table_id: Table ID
            record_ids: List of record IDs to update
            records: New values for records

        Returns:
            OperationPreview
        """
        affected_count = len(record_ids)

        # Fetch current values (limit to 10)
        preview_ids = record_ids[:10]
        query = f"SELECT * FROM {table_id} WHERE id IN ({','.join('?' * len(preview_ids))})"

        try:
            current_items = await self.grist_service.query_document(query, preview_ids)
        except Exception as e:
            logger.warning(f"Could not fetch current records: {e}")
            current_items = []

        # Build before/after preview
        affected_items = []
        for i, (record_id, new_values) in enumerate(zip(preview_ids, records[:10])):
            current = next((r for r in current_items if r.get("id") == record_id), {})
            affected_items.append(
                {
                    "id": record_id,
                    "before": current,
                    "after": {**current, **new_values},
                    "changes": list(new_values.keys()),
                }
            )

        warnings = []
        if affected_count > 10:
            warnings.append(
                f"⚠️ Modification massive : {affected_count} enregistrements seront modifiés"
            )

        return OperationPreview(
            operation_type=OperationType.UPDATE_RECORDS,
            description=f"Modifier {affected_count} enregistrement(s) dans la table '{table_id}'",
            affected_count=affected_count,
            affected_items=affected_items,
            warnings=warnings,
            is_reversible=False,  # Cannot auto-reverse, but data not deleted
        )

    async def preview_update_column_type(
        self, table_id: str, column_id: str, old_type: str, new_type: str
    ) -> OperationPreview:
        """
        Generate preview for column type change.

        Args:
            table_id: Table ID
            column_id: Column ID
            old_type: Current column type
            new_type: New column type

        Returns:
            OperationPreview
        """
        warnings = [
            f"⚠️ Changement du type de colonne de '{old_type}' vers '{new_type}'",
            "⚠️ Des données peuvent être perdues ou converties si incompatibles",
        ]

        # Check for potential data loss
        lossy_conversions = [
            ("Numeric", "Int"),  # Decimals will be truncated
            ("Text", "Int"),  # Non-numeric text will be lost
            ("Text", "Numeric"),  # Non-numeric text will be lost
            ("DateTime", "Date"),  # Time information will be lost
        ]

        if (old_type, new_type) in lossy_conversions:
            warnings.append(
                f"⚠️ PERTE DE DONNÉES POTENTIELLE : La conversion de {old_type} vers {new_type} peut perdre des informations"
            )

        return OperationPreview(
            operation_type=OperationType.UPDATE_COLUMN_TYPE,
            description=f"Changer le type de la colonne '{column_id}' de {old_type} vers {new_type}",
            affected_count=1,
            affected_items=[
                {
                    "table": table_id,
                    "column": column_id,
                    "old_type": old_type,
                    "new_type": new_type,
                }
            ],
            warnings=warnings,
            is_reversible=False,
        )
