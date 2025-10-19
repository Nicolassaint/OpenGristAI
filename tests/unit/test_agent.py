"""
Unit Tests for GristAgent

Tests for agent orchestration and execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.agent import GristAgent


@pytest.mark.unit
@pytest.mark.asyncio
class TestGristAgent:
    """Tests for GristAgent."""

    @pytest.fixture
    def agent(self, mock_grist_service, mock_llm):
        """Create a GristAgent with mocked dependencies."""
        with patch("app.core.agent.get_llm", return_value=mock_llm):
            agent = GristAgent(
                document_id="test-doc",
                grist_token="test-token",
                max_iterations=3,
                verbose=False,
            )
            # Replace the service with our mock
            agent.grist_service = mock_grist_service

            return agent

    async def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.document_id == "test-doc"
        assert agent.max_iterations == 3
        assert agent.verbose is False
        assert len(agent.tools) == 13
        assert agent.system_prompt is not None

    async def test_agent_cleanup(self, mock_grist_service, mock_llm):
        """Test agent cleanup."""
        with patch("app.core.agent.get_llm", return_value=mock_llm):
            agent = GristAgent(
                document_id="test-doc",
                grist_token="test-token",
                max_iterations=3,
                verbose=False,
            )
            # Mock the close method
            mock_grist_service.close = AsyncMock()
            agent.grist_service = mock_grist_service

            await agent.cleanup()
            mock_grist_service.close.assert_called_once()

    async def test_agent_run_simple_query(self, agent):
        """Test agent execution with simple query."""
        # Mock the LLM to return a response without tool calls
        from langchain_core.messages import AIMessage

        agent.llm_with_tools.ainvoke = AsyncMock(
            return_value=AIMessage(content="This document has 3 tables.")
        )

        result = await agent.run("What tables are in this document?")

        assert result["success"] is True
        assert "tables" in result["output"].lower()
        assert len(result["intermediate_steps"]) == 0  # No tool calls

    async def test_agent_run_with_tool_calls(self, agent, sample_tables):
        """Test agent execution with tool calls."""
        from langchain_core.messages import AIMessage

        # Mock LLM to first request tool call, then give final answer
        tool_call_response = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_tables",
                    "args": {},
                    "id": "call_123",
                }
            ],
        )
        final_response = AIMessage(
            content="The document has 3 tables: Students, Projects, and Grades."
        )

        agent.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[tool_call_response, final_response]
        )

        result = await agent.run("List all tables")

        assert result["success"] is True
        assert len(result["intermediate_steps"]) == 1
        assert result["intermediate_steps"][0][0]["name"] == "get_tables"

    async def test_agent_max_iterations(self, agent):
        """Test that agent stops at max iterations."""
        from langchain_core.messages import AIMessage

        # Mock LLM to always request tools (infinite loop)
        tool_call_response = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_tables",
                    "args": {},
                    "id": "call_123",
                }
            ],
        )

        agent.llm_with_tools.ainvoke = AsyncMock(return_value=tool_call_response)

        result = await agent.run("Test query")

        assert result["success"] is False
        assert "max iterations" in result["error"].lower()
        assert len(result["intermediate_steps"]) == agent.max_iterations

    async def test_agent_run_with_chat_history(self, agent):
        """Test agent with conversation history."""
        from langchain_core.messages import AIMessage

        agent.llm_with_tools.ainvoke = AsyncMock(
            return_value=AIMessage(content="Yes, I remember.")
        )

        chat_history = [
            {"role": "user", "content": "My name is John"},
            {"role": "assistant", "content": "Hello John!"},
        ]

        result = await agent.run("Do you remember my name?", chat_history=chat_history)

        assert result["success"] is True

    async def test_agent_update_context(self, agent):
        """Test updating agent context."""
        original_prompt = agent.system_prompt

        agent.update_context(page_name="new_page", page_id=2)

        assert agent.current_page_name == "new_page"
        assert agent.current_page_id == 2
        assert agent.system_prompt != original_prompt

    async def test_agent_tool_execution_error(self, agent):
        """Test agent handling of tool execution errors."""
        from langchain_core.messages import AIMessage

        # Mock LLM to request tool that will fail
        tool_call_response = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_table_columns",
                    "args": {"table_id": "NonExistent"},
                    "id": "call_123",
                }
            ],
        )
        final_response = AIMessage(content="There was an error accessing that table.")

        agent.llm_with_tools.ainvoke = AsyncMock(
            side_effect=[tool_call_response, final_response]
        )

        # Make the tool raise an error
        agent.grist_service.get_table_columns = AsyncMock(
            side_effect=ValueError("Table not found")
        )

        result = await agent.run("Get columns for NonExistent table")

        # Agent should handle the error gracefully
        assert len(result["intermediate_steps"]) > 0
        # Error should be in intermediate steps
        assert "Error" in str(result["intermediate_steps"][0][1])


@pytest.mark.unit
class TestAgentConfiguration:
    """Tests for agent configuration."""

    def test_agent_uses_settings(self):
        """Test that agent uses settings for configuration."""
        from app.models import settings

        with patch("app.core.agent.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm

            agent = GristAgent(
                document_id="test",
                grist_token="token",
            )

            # Should use settings values
            assert agent.max_iterations == settings.agent_max_iterations
            assert agent.base_url == settings.grist_base_url

    def test_agent_override_settings(self):
        """Test that agent can override settings."""
        with patch("app.core.agent.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm

            agent = GristAgent(
                document_id="test",
                grist_token="token",
                max_iterations=10,
                base_url="https://custom.grist.com",
            )

            # Should use override values
            assert agent.max_iterations == 10
            assert agent.base_url == "https://custom.grist.com"
