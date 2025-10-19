"""
Integration Tests for Agent Workflows

End-to-end tests for common agent workflows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.agent import GristAgent
from app.services.grist_service import GristService


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentWorkflows:
    """Integration tests for complete agent workflows."""

    @pytest.fixture
    def agent_with_mocks(self, mock_grist_service):
        """Create agent with mocked dependencies."""
        with patch("app.core.agent.get_llm") as mock_get_llm:
            # Create mock LLM
            mock_llm = MagicMock()
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm

            agent = GristAgent(
                document_id="test-doc",
                grist_token="test-token",
                max_iterations=5,
                verbose=False,
            )
            agent.grist_service = mock_grist_service
            agent.llm_with_tools = mock_llm

            return agent

    async def test_workflow_list_tables(self, agent_with_mocks, sample_tables):
        """Test workflow: list all tables."""
        from langchain_core.messages import AIMessage

        # Simulate LLM requesting get_tables tool
        tool_call = AIMessage(
            content="",
            tool_calls=[{"name": "get_tables", "args": {}, "id": "call_1"}],
        )
        final_response = AIMessage(
            content="This document has 3 tables: Students, Projects, and Grades."
        )

        agent_with_mocks.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[tool_call, final_response]
        )

        result = await agent_with_mocks.run("What tables are in this document?")

        assert result["success"] is True
        assert "tables" in result["output"].lower()
        assert len(result["intermediate_steps"]) == 1

    async def test_workflow_query_data(self, agent_with_mocks):
        """Test workflow: query data from a table."""
        from langchain_core.messages import AIMessage

        # Simulate LLM workflow: get tables -> get columns -> query
        get_tables_call = AIMessage(
            content="", tool_calls=[{"name": "get_tables", "args": {}, "id": "call_1"}]
        )
        get_columns_call = AIMessage(
            content="",
            tool_calls=[
                {"name": "get_table_columns", "args": {"table_id": "Students"}, "id": "call_2"}
            ],
        )
        query_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_document",
                    "args": {"query": "SELECT * FROM Students WHERE Age > 18"},
                    "id": "call_3",
                }
            ],
        )
        final_response = AIMessage(content="Found 2 students older than 18.")

        agent_with_mocks.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[get_tables_call, get_columns_call, query_call, final_response]
        )

        result = await agent_with_mocks.run("Show me students older than 18")

        assert result["success"] is True
        assert len(result["intermediate_steps"]) == 3

    async def test_workflow_add_record(self, agent_with_mocks):
        """Test workflow: add a new record."""
        from langchain_core.messages import AIMessage

        # Simulate LLM workflow: get columns -> add record
        get_columns_call = AIMessage(
            content="",
            tool_calls=[
                {"name": "get_table_columns", "args": {"table_id": "Students"}, "id": "call_1"}
            ],
        )
        add_record_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "add_records",
                    "args": {
                        "table_id": "Students",
                        "records": [{"Name": "Alice", "Age": 22}],
                    },
                    "id": "call_2",
                }
            ],
        )
        final_response = AIMessage(content="Added 1 student successfully.")

        agent_with_mocks.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[get_columns_call, add_record_call, final_response]
        )

        result = await agent_with_mocks.run("Add a student named Alice, age 22")

        assert result["success"] is True
        assert len(result["intermediate_steps"]) == 2

    async def test_workflow_with_sample_data(self, agent_with_mocks):
        """Test workflow: using sample data before querying."""
        from langchain_core.messages import AIMessage

        # Best practice: get sample records before querying
        get_sample_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_sample_records",
                    "args": {"table_id": "Students", "limit": 5},
                    "id": "call_1",
                }
            ],
        )
        query_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_document",
                    "args": {"query": "SELECT * FROM Students WHERE Grade = 'A'"},
                    "id": "call_2",
                }
            ],
        )
        final_response = AIMessage(content="Found 2 students with grade A.")

        agent_with_mocks.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[get_sample_call, query_call, final_response]
        )

        result = await agent_with_mocks.run("Show me all students with grade A")

        assert result["success"] is True
        # Should have used sample data first
        assert result["intermediate_steps"][0][0]["name"] == "get_sample_records"

    async def test_workflow_multi_step(self, agent_with_mocks):
        """Test complex multi-step workflow."""
        from langchain_core.messages import AIMessage

        # Complex workflow: query -> update -> verify
        query_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_document",
                    "args": {"query": "SELECT * FROM Students WHERE Name = 'John Doe'"},
                    "id": "call_1",
                }
            ],
        )
        update_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "update_records",
                    "args": {
                        "table_id": "Students",
                        "record_ids": [1],
                        "records": [{"Grade": "A+"}],
                    },
                    "id": "call_2",
                }
            ],
        )
        verify_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_document",
                    "args": {"query": "SELECT * FROM Students WHERE id = 1"},
                    "id": "call_3",
                }
            ],
        )
        final_response = AIMessage(content="Updated John Doe's grade to A+.")

        agent_with_mocks.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[query_call, update_call, verify_call, final_response]
        )

        result = await agent_with_mocks.run(
            "Update John Doe's grade to A+ and verify"
        )

        assert result["success"] is True
        assert len(result["intermediate_steps"]) == 3

    async def test_workflow_with_conversation_history(self, agent_with_mocks):
        """Test workflow with conversation context."""
        from langchain_core.messages import AIMessage

        chat_history = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Hello Alice!"},
        ]

        final_response = AIMessage(content="Yes, your name is Alice.")

        agent_with_mocks.llm_with_tools.ainvoke = AsyncMock(
            return_value=final_response
        )

        result = await agent_with_mocks.run(
            "What is my name?", chat_history=chat_history
        )

        assert result["success"] is True
        # Should have access to conversation history
        assert "Alice" in result["output"]


@pytest.mark.integration
class TestErrorRecoveryWorkflows:
    """Tests for error recovery in agent workflows."""

    @pytest.mark.asyncio
    async def test_recovery_from_tool_error(self, mock_grist_client):
        """Test agent recovers from tool execution error."""
        from langchain_core.messages import AIMessage

        with patch("app.core.agent.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm

            # Create service with mock client
            service = GristService(
                document_id="test",
                access_token="token",
                enable_validation=False,
            )
            service.client = mock_grist_client

            agent = GristAgent(
                document_id="test",
                grist_token="token",
                max_iterations=3,
            )
            agent.grist_service = service
            agent.llm_with_tools = mock_llm

            # Simulate error then recovery
            error_call = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_table_columns",
                        "args": {"table_id": "NonExistent"},
                        "id": "call_1",
                    }
                ],
            )
            recovery_call = AIMessage(
                content="", tool_calls=[{"name": "get_tables", "args": {}, "id": "call_2"}]
            )
            final_response = AIMessage(
                content="That table doesn't exist. Available tables are Students and Projects."
            )

            agent.llm_with_tools.ainvoke = AsyncMock(
                side_effect=[error_call, recovery_call, final_response]
            )

            # Make first tool call fail
            service.get_table_columns = AsyncMock(
                side_effect=ValueError("Table not found")
            )

            result = await agent.run("Get columns for NonExistent table")

            # Agent should recover and provide useful response
            assert result["success"] is True

            await agent.cleanup()
