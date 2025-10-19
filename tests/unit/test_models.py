"""
Unit Tests for Pydantic Models

Tests for data validation and serialization in API and data models.
"""

import pytest
from pydantic import ValidationError

from app.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ToolCall,
    UIMessage,
    Column,
    ColumnFields,
    Record,
    Table,
    TableInfo,
)


class TestAPIModels:
    """Tests for API request/response models."""

    def test_ui_message_valid(self):
        """Test valid UIMessage creation."""
        message = UIMessage(
            id="msg-1",
            role="user",
            parts=[{"type": "text", "text": "Hello"}],
        )
        assert message.id == "msg-1"
        assert message.role == "user"
        assert len(message.parts) == 1

    def test_ui_message_with_content(self):
        """Test UIMessage with legacy content field."""
        message = UIMessage(
            id="msg-2", role="assistant", content="Hello back"
        )
        assert message.content == "Hello back"
        assert message.parts is None

    def test_chat_request_valid(self, sample_chat_request):
        """Test valid ChatRequest creation."""
        request = ChatRequest(**sample_chat_request)
        assert request.documentId == "test-document"
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"

    def test_chat_request_missing_document_id(self):
        """Test ChatRequest validation fails without document ID."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(messages=[])

        assert "documentId" in str(exc_info.value)

    def test_chat_response_valid(self):
        """Test valid ChatResponse creation."""
        response = ChatResponse(
            response="Hello",
            agent_used="gpt-4o-mini",
            tool_calls=[
                ToolCall(
                    tool_name="get_tables",
                    tool_input={},
                    tool_output=[{"id": "Table1"}],
                )
            ],
        )
        assert response.response == "Hello"
        assert len(response.tool_calls) == 1
        assert response.error is None

    def test_health_response(self):
        """Test HealthResponse creation."""
        health = HealthResponse(status="healthy", version="0.1.0")
        assert health.status == "healthy"
        assert health.version == "0.1.0"

    def test_tool_call_valid(self):
        """Test ToolCall creation."""
        tool_call = ToolCall(
            tool_name="query_document",
            tool_input={"query": "SELECT * FROM Table1"},
            tool_output=[{"id": 1, "name": "John"}],
        )
        assert tool_call.tool_name == "query_document"
        assert "query" in tool_call.tool_input


class TestGristModels:
    """Tests for Grist data models."""

    def test_table_info_valid(self):
        """Test TableInfo creation."""
        table = TableInfo(id="Students", label="Students")
        assert table.id == "Students"
        assert table.label == "Students"

    def test_table_info_without_label(self):
        """Test TableInfo without label."""
        table = TableInfo(id="Students")
        assert table.id == "Students"
        assert table.label is None

    def test_column_fields_valid(self):
        """Test ColumnFields creation."""
        fields = ColumnFields(
            type="Text",
            label="Full Name",
            formula=None,
            widgetOptions=None,
        )
        assert fields.type == "Text"
        assert fields.label == "Full Name"

    def test_column_with_widget_options(self):
        """Test Column with widget options."""
        column = Column(
            id="Grade",
            fields=ColumnFields(
                type="Choice",
                label="Grade",
                widgetOptions={"choices": ["A", "B", "C"]},
            ),
        )
        assert column.id == "Grade"
        assert column.fields.type == "Choice"
        assert "choices" in column.fields.widgetOptions

    def test_record_valid(self):
        """Test Record creation."""
        record = Record(
            id=1,
            fields={"Name": "John Doe", "Age": 30},
        )
        assert record.id == 1
        assert record.fields["Name"] == "John Doe"
        assert record.fields["Age"] == 30

    def test_table_with_columns(self):
        """Test Table with columns."""
        table = Table(
            id="Students",
            label="Students",
            columns=[
                Column(
                    id="Name",
                    fields=ColumnFields(type="Text", label="Full Name"),
                ),
                Column(
                    id="Age",
                    fields=ColumnFields(type="Int", label="Age"),
                ),
            ],
        )
        assert table.id == "Students"
        assert len(table.columns) == 2
        assert table.columns[0].id == "Name"


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_chat_request_from_json(self, sample_chat_request):
        """Test ChatRequest deserialization from JSON."""
        request = ChatRequest(**sample_chat_request)
        # Convert back to dict
        data = request.model_dump()
        assert data["documentId"] == "test-document"
        assert len(data["messages"]) == 1

    def test_chat_response_to_json(self):
        """Test ChatResponse serialization to JSON."""
        response = ChatResponse(
            response="Test response",
            sql_query="SELECT * FROM Table1",
        )
        data = response.model_dump()
        assert "response" in data
        assert "sql_query" in data
        assert data["error"] is None

    def test_record_serialization(self):
        """Test Record serialization."""
        record = Record(id=1, fields={"Name": "John", "Age": 30})
        data = record.model_dump()
        assert data["id"] == 1
        assert data["fields"]["Name"] == "John"
