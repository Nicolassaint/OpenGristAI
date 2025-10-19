"""
Unit Tests for LangChain Tools

Tests for Grist tools used by the agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.core.tools import (
    get_all_tools,
    get_tables,
    get_table_columns,
    get_sample_records,
    query_document,
    add_records,
    update_records,
    remove_records,
    set_grist_service,
    get_grist_service,
)


@pytest.mark.unit
class TestToolRegistry:
    """Tests for tool registry and configuration."""

    def test_get_all_tools(self):
        """Test that all tools are returned."""
        tools = get_all_tools()
        assert len(tools) == 13  # Total number of tools

        tool_names = [tool.name for tool in tools]
        assert "get_tables" in tool_names
        assert "get_table_columns" in tool_names
        assert "query_document" in tool_names
        assert "add_records" in tool_names
        assert "update_records" in tool_names

    def test_tool_metadata(self):
        """Test that tools have proper metadata."""
        tools = get_all_tools()

        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert tool.name  # Not empty
            assert tool.description  # Not empty


@pytest.mark.unit
@pytest.mark.asyncio
class TestToolExecution:
    """Tests for individual tool execution."""

    async def test_get_tables_tool(self, mock_grist_service, sample_tables):
        """Test get_tables tool."""
        set_grist_service(mock_grist_service)

        result = await get_tables.ainvoke({})
        assert len(result) == 3
        assert result[0]["id"] == "Students"

    async def test_get_table_columns_tool(
        self, mock_grist_service, sample_columns
    ):
        """Test get_table_columns tool."""
        set_grist_service(mock_grist_service)

        result = await get_table_columns.ainvoke({"table_id": "Students"})
        assert len(result) == 5
        assert result[1]["id"] == "Name"

    async def test_get_sample_records_tool(
        self, mock_grist_service, sample_records
    ):
        """Test get_sample_records tool."""
        set_grist_service(mock_grist_service)

        result = await get_sample_records.ainvoke(
            {"table_id": "Students", "limit": 5}
        )
        assert len(result) > 0
        assert len(result) <= 10  # Max limit enforced

    async def test_query_document_tool(self, mock_grist_service):
        """Test query_document tool."""
        set_grist_service(mock_grist_service)

        result = await query_document.ainvoke(
            {"query": "SELECT * FROM Students WHERE Age > 18"}
        )
        assert isinstance(result, list)

    async def test_query_document_with_args(self, mock_grist_service):
        """Test query_document tool with arguments."""
        set_grist_service(mock_grist_service)

        result = await query_document.ainvoke(
            {"query": "SELECT * FROM Students WHERE Age > ?", "args": [18]}
        )
        assert isinstance(result, list)

    async def test_add_records_tool(self, mock_grist_service):
        """Test add_records tool."""
        set_grist_service(mock_grist_service)

        result = await add_records.ainvoke(
            {
                "table_id": "Students",
                "records": [
                    {"Name": "Alice", "Age": 22},
                    {"Name": "Bob", "Age": 23},
                ],
            }
        )
        assert "record_ids" in result
        assert result["count"] == 2

    async def test_update_records_tool(self, mock_grist_service):
        """Test update_records tool."""
        set_grist_service(mock_grist_service)

        result = await update_records.ainvoke(
            {
                "table_id": "Students",
                "record_ids": [1, 2],
                "records": [
                    {"Name": "Updated 1"},
                    {"Name": "Updated 2"},
                ],
            }
        )
        assert "updated_count" in result

    async def test_remove_records_tool(self, mock_grist_service):
        """Test remove_records tool."""
        set_grist_service(mock_grist_service)

        result = await remove_records.ainvoke(
            {"table_id": "Students", "record_ids": [1, 2]}
        )
        assert "deleted_count" in result

    async def test_tool_without_service_raises(self):
        """Test that tools raise error when service not set."""
        # Clear service
        from app.core.tools import _grist_service

        _grist_service.set(None)

        with pytest.raises(RuntimeError) as exc_info:
            get_grist_service()

        assert "GristService not configured" in str(exc_info.value)


@pytest.mark.unit
class TestToolInputSchemas:
    """Tests for tool input validation."""

    def test_get_table_columns_input_valid(self):
        """Test GetTableColumnsInput validation."""
        from app.models import GetTableColumnsInput

        input_data = GetTableColumnsInput(table_id="Students")
        assert input_data.table_id == "Students"

    def test_query_document_input_valid(self):
        """Test QueryDocumentInput validation."""
        from app.models import QueryDocumentInput

        input_data = QueryDocumentInput(
            query="SELECT * FROM Students", args=[18]
        )
        assert input_data.query == "SELECT * FROM Students"
        assert input_data.args == [18]

    def test_add_records_input_valid(self):
        """Test AddRecordsInput validation."""
        from app.models import AddRecordsInput

        input_data = AddRecordsInput(
            table_id="Students",
            records=[{"Name": "Alice", "Age": 22}],
        )
        assert input_data.table_id == "Students"
        assert len(input_data.records) == 1

    def test_update_records_input_valid(self):
        """Test UpdateRecordsInput validation."""
        from app.models import UpdateRecordsInput

        input_data = UpdateRecordsInput(
            table_id="Students",
            record_ids=[1, 2],
            records=[{"Name": "Updated"}],
        )
        assert input_data.table_id == "Students"
        assert len(input_data.record_ids) == 2
