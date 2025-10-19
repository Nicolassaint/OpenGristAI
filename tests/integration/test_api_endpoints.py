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
class TestConfirmEndpoint:
    """Tests for /chat/confirm endpoint."""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Clear confirmation service before and after each test."""
        from app.services.confirmation_service import get_confirmation_service

        service = get_confirmation_service()
        service.clear_all()
        yield
        service.clear_all()

    def test_confirm_operation_reject(self, api_client, sample_headers):
        """Test rejecting a confirmation."""
        from app.models import (
            ConfirmationDecision,
            ConfirmationStatus,
            OperationPreview,
            OperationType,
        )
        from app.services.confirmation_service import get_confirmation_service

        # Create a pending confirmation
        service = get_confirmation_service()
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Delete 5 records",
            affected_count=5,
            warnings=["Irreversible"],
            is_reversible=False,
        )

        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={"table_id": "Students", "record_ids": [1, 2, 3, 4, 5]},
            preview=preview,
        )

        # Reject it
        decision = ConfirmationDecision(
            confirmation_id=confirmation.confirmation_id,
            approved=False,
            reason="Changed my mind",
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ConfirmationStatus.REJECTED
        assert "cancelled" in data["message"].lower()

        # Should be removed from pending
        assert service.get_pending_count() == 0

    @patch("app.api.routes.get_all_tools")
    def test_confirm_operation_approve(
        self, mock_get_tools, api_client, sample_headers
    ):
        """Test approving and executing a confirmation."""
        from app.models import (
            ConfirmationDecision,
            ConfirmationStatus,
            OperationPreview,
            OperationType,
        )
        from app.services.confirmation_service import get_confirmation_service

        # Create a pending confirmation
        service = get_confirmation_service()
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Delete 2 records",
            affected_count=2,
            warnings=["Irreversible"],
            is_reversible=False,
        )

        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={
                "table_id": "Students",
                "record_ids": [1, 2],
                "document_id": "test-doc",
            },
            preview=preview,
        )

        # Mock the tool
        mock_tool = AsyncMock()
        mock_tool.name = "remove_records"
        mock_tool.ainvoke = AsyncMock(return_value={"deleted_count": 2})
        mock_get_tools.return_value = [mock_tool]

        # Approve it
        decision = ConfirmationDecision(
            confirmation_id=confirmation.confirmation_id,
            approved=True,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ConfirmationStatus.APPROVED
        assert "completed successfully" in data["message"].lower()
        assert data["result"]["deleted_count"] == 2

        # Should be removed from pending
        assert service.get_pending_count() == 0

        # Tool should have been called
        mock_tool.ainvoke.assert_called_once()

    def test_confirm_operation_not_found(self, api_client, sample_headers):
        """Test confirming non-existent confirmation."""
        from app.models import ConfirmationDecision

        decision = ConfirmationDecision(
            confirmation_id="conf_doesnotexist",
            approved=True,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_confirm_operation_expired(self, api_client, sample_headers):
        """Test confirming expired confirmation."""
        from app.models import (
            ConfirmationDecision,
            OperationPreview,
            OperationType,
        )
        from app.services.confirmation_service import get_confirmation_service

        # Create a confirmation that expires immediately
        service = get_confirmation_service()
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Delete records",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={},
            preview=preview,
            expires_in_seconds=0,  # Expire immediately
        )

        # Try to approve
        decision = ConfirmationDecision(
            confirmation_id=confirmation.confirmation_id,
            approved=True,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found or expired" in response.json()["detail"].lower()

    def test_confirm_operation_reject_not_found(self, api_client, sample_headers):
        """Test rejecting non-existent confirmation."""
        from app.models import ConfirmationDecision

        decision = ConfirmationDecision(
            confirmation_id="conf_doesnotexist",
            approved=False,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.api.routes.get_all_tools")
    def test_confirm_operation_tool_not_found(
        self, mock_get_tools, api_client, sample_headers
    ):
        """Test approving when tool doesn't exist."""
        from app.models import (
            ConfirmationDecision,
            OperationPreview,
            OperationType,
        )
        from app.services.confirmation_service import get_confirmation_service

        service = get_confirmation_service()
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Delete records",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="nonexistent_tool",
            tool_args={"document_id": "test"},
            preview=preview,
        )

        # Mock no tools found
        mock_get_tools.return_value = []

        decision = ConfirmationDecision(
            confirmation_id=confirmation.confirmation_id,
            approved=True,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "not found" in response.json()["detail"].lower()

    @patch("app.api.routes.get_all_tools")
    def test_confirm_operation_tool_execution_error(
        self, mock_get_tools, api_client, sample_headers
    ):
        """Test handling tool execution errors."""
        from app.models import (
            ConfirmationDecision,
            ConfirmationStatus,
            OperationPreview,
            OperationType,
        )
        from app.services.confirmation_service import get_confirmation_service

        service = get_confirmation_service()
        preview = OperationPreview(
            operation_type=OperationType.DELETE_RECORDS,
            description="Delete records",
            affected_count=1,
            warnings=[],
            is_reversible=False,
        )

        confirmation = service.create_confirmation(
            operation_type=OperationType.DELETE_RECORDS,
            tool_name="remove_records",
            tool_args={"table_id": "Students", "document_id": "test"},
            preview=preview,
        )

        # Mock tool that raises error
        mock_tool = AsyncMock()
        mock_tool.name = "remove_records"
        mock_tool.ainvoke = AsyncMock(side_effect=Exception("Database error"))
        mock_get_tools.return_value = [mock_tool]

        decision = ConfirmationDecision(
            confirmation_id=confirmation.confirmation_id,
            approved=True,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
            headers=sample_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ConfirmationStatus.APPROVED
        assert "failed" in data["message"].lower()

    def test_confirm_operation_missing_api_key(self, api_client):
        """Test endpoint requires API key."""
        from app.models import ConfirmationDecision

        decision = ConfirmationDecision(
            confirmation_id="conf_test",
            approved=True,
        )

        response = api_client.post(
            "/chat/confirm",
            json=decision.model_dump(),
        )

        # Should fail without x-api-key header
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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
