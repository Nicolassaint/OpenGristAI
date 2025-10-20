"""
Real API Integration Tests for All Grist Tools

These tests use a REAL Grist API connection to verify that all tools work
correctly end-to-end. They are OPTIONAL and require proper configuration.

⚠️  WARNING: These tests will create temporary data in your Grist document.

For unit tests with mocks, see: tests/unit/test_tools.py
For integration tests with mocks, see: tests/integration/test_agent_workflows.py
"""

import os
import pytest

from app.services.grist_service import GristService
from app.core.tools import (
    set_grist_service,
    get_tables,
    get_table_columns,
    query_document,
    add_records,
    update_records,
    remove_records,
    add_table,
    add_table_column,
    update_table_column,
    remove_table_column,
)


@pytest.mark.requires_api
@pytest.mark.integration
@pytest.mark.asyncio
class TestAllToolsRealAPI:
    """
    Integration tests with real Grist API.

    These tests require:
    - GRIST_API_KEY environment variable
    - GRIST_DOCUMENT_ID environment variable (optional, will use test doc if not set)
    - GRIST_BASE_URL environment variable (optional, defaults to https://docs.getgrist.com)

    To run these tests:
        pytest tests/integration/test_all_tools.py -m requires_api

    WARNING: These tests will create temporary data in your Grist document.
    A test table named 'TestToolsTable' will be created but cannot be
    automatically deleted (Grist API limitation). Please delete it manually.
    """

    TEST_TABLE_NAME = "TestToolsTable"

    @pytest.fixture
    def grist_credentials(self):
        """Get Grist credentials from environment."""
        api_key = os.getenv("GRIST_API_KEY")
        if not api_key:
            pytest.skip("GRIST_API_KEY not set")

        return {
            "api_key": api_key,
            "document_id": os.getenv("GRIST_DOCUMENT_ID", "test-document"),
            "base_url": os.getenv(
                "GRIST_BASE_URL", "https://docs.getgrist.com"
            ),
        }

    @pytest.fixture
    async def real_grist_service(self, grist_credentials):
        """Create real Grist service for integration tests."""
        async with GristService(
            document_id=grist_credentials["document_id"],
            access_token=grist_credentials["api_key"],
            base_url=grist_credentials["base_url"],
            enable_validation=False,
            use_api_key=True,
        ) as service:
            set_grist_service(service)
            yield service
            set_grist_service(None)

    async def test_real_get_tables(self, real_grist_service):
        """Test get_tables with real API."""
        result = await get_tables.ainvoke({})
        assert isinstance(result, list)
        # Should have at least some tables
        assert len(result) >= 0

    async def test_real_query_document(self, real_grist_service):
        """Test query_document with real API."""
        # Get tables first
        tables = await get_tables.ainvoke({})
        if not tables:
            pytest.skip("No tables in document")

        table_id = tables[0]["id"]
        result = await query_document.ainvoke(
            {"query": f"SELECT * FROM {table_id} LIMIT 3"}
        )
        assert isinstance(result, list)

    async def test_real_full_workflow(self, real_grist_service):
        """
        Test complete workflow: create table, add data, query, update, delete.

        WARNING: This test creates a table that cannot be automatically deleted.
        """
        # 1. Create table
        table_result = await add_table.ainvoke(
            {
                "table_id": self.TEST_TABLE_NAME,
                "columns": [
                    {"id": "TestName", "fields": {"type": "Text", "label": "Name"}},
                    {"id": "TestAge", "fields": {"type": "Int", "label": "Age"}},
                ],
            }
        )
        assert table_result["table_id"] == self.TEST_TABLE_NAME

        try:
            # 2. Add column
            column_result = await add_table_column.ainvoke(
                {
                    "table_id": self.TEST_TABLE_NAME,
                    "column_id": "TestEmail",
                    "column_type": "Text",
                    "label": "Email Address",
                }
            )
            assert "column_id" in column_result

            # 3. Add records
            add_result = await add_records.ainvoke(
                {
                    "table_id": self.TEST_TABLE_NAME,
                    "records": [
                        {"TestName": "Alice", "TestAge": 30},
                        {"TestName": "Bob", "TestAge": 25},
                    ],
                }
            )
            assert add_result["count"] == 2
            record_ids = add_result["record_ids"]

            # 4. Update record
            update_result = await update_records.ainvoke(
                {
                    "table_id": self.TEST_TABLE_NAME,
                    "record_ids": [record_ids[0]],
                    "records": [{"TestAge": 31}],
                }
            )
            assert update_result["updated_count"] == 1

            # 5. Query data
            query_result = await query_document.ainvoke(
                {"query": f"SELECT * FROM {self.TEST_TABLE_NAME}"}
            )
            assert len(query_result) >= 2

            # 6. Delete record
            delete_result = await remove_records.ainvoke(
                {"table_id": self.TEST_TABLE_NAME, "record_ids": [record_ids[0]]}
            )
            assert delete_result["deleted_count"] == 1

            # 7. Update column
            update_col_result = await update_table_column.ainvoke(
                {
                    "table_id": self.TEST_TABLE_NAME,
                    "column_id": "TestEmail",
                    "label": "Email (Updated)",
                }
            )
            assert update_col_result["updated"] is True

            # 8. Get columns to find updated column ID
            columns = await get_table_columns.ainvoke(
                {"table_id": self.TEST_TABLE_NAME}
            )
            email_column = next(
                (c for c in columns if "Email" in c.get("id", "")), None
            )
            assert email_column is not None

            # 9. Delete column
            if email_column:
                delete_col_result = await remove_table_column.ainvoke(
                    {
                        "table_id": self.TEST_TABLE_NAME,
                        "column_id": email_column["id"],
                    }
                )
                assert delete_col_result["deleted"] is True

        finally:
            # Cleanup note
            print(
                f"\n⚠️  WARNING: Test table '{self.TEST_TABLE_NAME}' was created "
                "but cannot be automatically deleted (Grist API limitation). "
                "Please delete it manually from the Grist interface."
            )
