"""
Integration Tests for API Endpoints

Tests for FastAPI endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import status


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.integration
class TestChatEndpoint:
    """Tests for /chat endpoint."""

    def test_chat_missing_api_key(self, api_client, sample_chat_request):
        """Test chat endpoint without API key."""
        response = api_client.post("/chat", json=sample_chat_request)

        # Should fail without x-api-key header
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.api.routes.GristAgent")
    def test_chat_success(
        self, mock_agent_class, api_client, sample_chat_request, sample_headers
    ):
        """Test successful chat request."""
        # Mock the agent
        mock_agent = AsyncMock()
        mock_agent.run.return_value = {
            "output": "This document has 3 tables.",
            "intermediate_steps": [],
            "success": True,
        }
        mock_agent.cleanup = AsyncMock()
        mock_agent_class.return_value = mock_agent

        response = api_client.post(
            "/chat", json=sample_chat_request, headers=sample_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert data["response"] == "This document has 3 tables."

    @patch("app.api.routes.GristAgent")
    def test_chat_with_tool_calls(
        self, mock_agent_class, api_client, sample_chat_request, sample_headers
    ):
        """Test chat request with tool calls."""
        # Mock agent with tool calls
        mock_agent = AsyncMock()
        mock_agent.run.return_value = {
            "output": "The document has these tables: Students, Projects.",
            "intermediate_steps": [
                (
                    {"name": "get_tables", "args": {}, "id": "call_1"},
                    [{"id": "Students"}, {"id": "Projects"}],
                )
            ],
            "success": True,
        }
        mock_agent.cleanup = AsyncMock()
        mock_agent_class.return_value = mock_agent

        response = api_client.post(
            "/chat", json=sample_chat_request, headers=sample_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tool_calls" in data
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool_name"] == "get_tables"

    @patch("app.api.routes.GristAgent")
    def test_chat_with_sql_query(
        self, mock_agent_class, api_client, sample_headers
    ):
        """Test chat request that executes SQL query."""
        # Request with query
        request_data = {
            "messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": "Show me all students older than 18",
                        }
                    ],
                }
            ],
            "documentId": "test-doc",
        }

        # Mock agent with SQL query
        mock_agent = AsyncMock()
        mock_agent.run.return_value = {
            "output": "Found 2 students.",
            "intermediate_steps": [
                (
                    {
                        "name": "query_document",
                        "args": {"query": "SELECT * FROM Students WHERE Age > 18"},
                        "id": "call_1",
                    },
                    [{"id": 1, "Name": "John"}],
                )
            ],
            "success": True,
        }
        mock_agent.cleanup = AsyncMock()
        mock_agent_class.return_value = mock_agent

        response = api_client.post(
            "/chat", json=request_data, headers=sample_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sql_query"] == "SELECT * FROM Students WHERE Age > 18"

    def test_chat_no_user_message(self, api_client, sample_headers):
        """Test chat request with no user message."""
        request_data = {
            "messages": [],
            "documentId": "test-doc",
        }

        response = api_client.post(
            "/chat", json=request_data, headers=sample_headers
        )

        # Should return 400 for no user message
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("app.api.routes.GristAgent")
    def test_chat_agent_error(
        self, mock_agent_class, api_client, sample_chat_request, sample_headers
    ):
        """Test chat request when agent encounters an error."""
        # Mock agent to return error
        mock_agent = AsyncMock()
        mock_agent.run.return_value = {
            "output": "I encountered an error.",
            "intermediate_steps": [],
            "success": False,
            "error": "Table not found",
        }
        mock_agent.cleanup = AsyncMock()
        mock_agent_class.return_value = mock_agent

        response = api_client.post(
            "/chat", json=sample_chat_request, headers=sample_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["error"] == "Table not found"

    def test_chat_with_content_field(self, api_client, sample_headers):
        """Test chat with legacy content field instead of parts."""
        request_data = {
            "messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "content": "What tables are in this document?",
                }
            ],
            "documentId": "test-doc",
        }

        with patch("app.api.routes.GristAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.run.return_value = {
                "output": "Response",
                "intermediate_steps": [],
                "success": True,
            }
            mock_agent.cleanup = AsyncMock()
            mock_agent_class.return_value = mock_agent

            response = api_client.post(
                "/chat", json=request_data, headers=sample_headers
            )

            assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, api_client):
        """Test root endpoint returns API info."""
        response = api_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Grist AI Assistant API"
