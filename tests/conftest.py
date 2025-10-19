"""
Pytest Configuration and Shared Fixtures

This file contains fixtures that are available to all tests.
"""

import os
import pytest
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["ENVIRONMENT"] = "testing"
os.environ["GRIST_BASE_URL"] = "https://test.grist.com"

from app.api.main import app
from app.models import Settings
from app.services.grist_client import GristAPIClient
from app.services.grist_service import GristService


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with safe defaults."""
    return Settings(
        environment="testing",
        log_level="DEBUG",
        openai_api_key="test-api-key",
        openai_model="gpt-4o-mini",
        grist_base_url="https://test.grist.com",
        agent_max_iterations=5,
        agent_verbose=False,
    )


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_tables() -> List[Dict[str, Any]]:
    """Sample Grist tables for testing."""
    return [
        {"id": "Students", "label": "Students"},
        {"id": "Projects", "label": "Projects"},
        {"id": "Grades", "label": "Grades"},
    ]


@pytest.fixture
def sample_columns() -> Dict[str, List[Dict[str, Any]]]:
    """Sample columns for each table."""
    return {
        "Students": [
            {"id": "id", "fields": {"type": "Int", "label": "ID"}},
            {"id": "Name", "fields": {"type": "Text", "label": "Full Name"}},
            {"id": "Email", "fields": {"type": "Text", "label": "Email"}},
            {"id": "Age", "fields": {"type": "Int", "label": "Age"}},
            {
                "id": "Grade",
                "fields": {
                    "type": "Choice",
                    "label": "Grade",
                    "widgetOptions": {"choices": ["A", "B", "C", "D", "F"]},
                },
            },
        ],
        "Projects": [
            {"id": "id", "fields": {"type": "Int", "label": "ID"}},
            {"id": "Title", "fields": {"type": "Text", "label": "Title"}},
            {"id": "Description", "fields": {"type": "Text", "label": "Description"}},
            {"id": "StudentId", "fields": {"type": "Ref", "label": "Student"}},
        ],
    }


@pytest.fixture
def sample_records() -> Dict[str, List[Dict[str, Any]]]:
    """Sample records for each table."""
    return {
        "Students": [
            {
                "id": 1,
                "fields": {
                    "Name": "John Doe",
                    "Email": "john@example.com",
                    "Age": 20,
                    "Grade": "A",
                },
            },
            {
                "id": 2,
                "fields": {
                    "Name": "Jane Smith",
                    "Email": "jane@example.com",
                    "Age": 21,
                    "Grade": "B",
                },
            },
            {
                "id": 3,
                "fields": {
                    "Name": "Bob Johnson",
                    "Email": "bob@example.com",
                    "Age": 19,
                    "Grade": "A",
                },
            },
        ],
        "Projects": [
            {
                "id": 1,
                "fields": {
                    "Title": "Final Project",
                    "Description": "Capstone project",
                    "StudentId": 1,
                },
            },
            {
                "id": 2,
                "fields": {
                    "Title": "Research Paper",
                    "Description": "Literature review",
                    "StudentId": 2,
                },
            },
        ],
    }


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_grist_client(sample_tables, sample_columns, sample_records):
    """Mock GristAPIClient with sample data."""
    mock_client = AsyncMock(spec=GristAPIClient)

    # Mock get_tables
    mock_client.get_tables.return_value = sample_tables

    # Mock get_table_columns
    async def get_table_columns(table_id: str):
        return sample_columns.get(table_id, [])

    mock_client.get_table_columns.side_effect = get_table_columns

    # Mock get_records
    async def get_records(table_id: str, limit: int = None):
        records = sample_records.get(table_id, [])
        return records[:limit] if limit else records

    mock_client.get_records.side_effect = get_records

    # Mock query_sql
    async def query_sql(query: str, args: List = None):
        # Simple mock: return all students for any query
        return sample_records.get("Students", [])

    mock_client.query_sql.side_effect = query_sql

    # Mock add_records
    async def add_records(table_id: str, records: List[Dict[str, Any]]):
        return {
            "records": [
                {"id": i + 100, **record} for i, record in enumerate(records)
            ]
        }

    mock_client.add_records.side_effect = add_records

    # Mock update_records
    async def update_records(table_id: str, records: List[Dict[str, Any]]):
        return {"updated": len(records)}

    mock_client.update_records.side_effect = update_records

    # Mock delete_records
    async def delete_records(table_id: str, record_ids: List[int]):
        return {"deleted": len(record_ids)}

    mock_client.delete_records.side_effect = delete_records

    # Mock add_table
    async def add_table(table_id: str, columns: List[Dict[str, Any]]):
        return {"table_id": table_id, "columns": len(columns)}

    mock_client.add_table.side_effect = add_table

    # Mock add_column
    async def add_column(table_id: str, column_id: str, fields: Dict[str, Any]):
        return {"column_id": column_id}

    mock_client.add_column.side_effect = add_column

    # Mock update_column
    async def update_column(table_id: str, column_id: str, fields: Dict[str, Any]):
        return {"updated": True}

    mock_client.update_column.side_effect = update_column

    # Mock delete_column
    async def delete_column(table_id: str, column_id: str):
        return {"deleted": True}

    mock_client.delete_column.side_effect = delete_column

    # Mock close
    mock_client.close = AsyncMock()

    return mock_client


@pytest.fixture
def mock_grist_service(mock_grist_client, sample_tables, sample_columns, sample_records):
    """Mock GristService with sample data."""
    service = GristService(
        document_id="test-doc",
        access_token="test-token",
        base_url="https://test.grist.com",
        enable_validation=False,  # Disable validation for basic tests
    )

    # Replace the client with our mock
    service.client = mock_grist_client

    return service


@pytest.fixture
def mock_llm():
    """Mock LangChain LLM for agent testing."""
    with patch("app.core.llm.ChatOpenAI") as mock:
        # Create a mock LLM instance
        mock_instance = MagicMock()

        # Mock ainvoke to return a simple AIMessage
        async def ainvoke(messages):
            from langchain_core.messages import AIMessage

            return AIMessage(content="Mock LLM response")

        mock_instance.ainvoke = ainvoke

        # Mock bind_tools to return itself
        mock_instance.bind_tools = MagicMock(return_value=mock_instance)

        # Configure the mock to return our instance
        mock.return_value = mock_instance

        yield mock_instance


# ============================================================================
# API Test Fixtures
# ============================================================================


@pytest.fixture
def api_client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_chat_request() -> Dict[str, Any]:
    """Sample chat request payload."""
    return {
        "messages": [
            {
                "id": "msg-1",
                "role": "user",
                "parts": [{"type": "text", "text": "What tables are in this document?"}],
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ],
        "documentId": "test-document",
    }


@pytest.fixture
def sample_headers() -> Dict[str, str]:
    """Sample HTTP headers for API requests."""
    return {
        "x-api-key": "test-grist-token",
        "content-type": "application/json",
    }


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_api: Tests requiring real API access")


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio

    return asyncio.get_event_loop_policy()


# ============================================================================
# Helper Functions
# ============================================================================


@pytest.fixture
def assert_valid_record():
    """Helper to assert a record has required fields."""

    def _assert(record: Dict[str, Any], required_fields: List[str] = None):
        assert "id" in record or "fields" in record, "Record must have 'id' or 'fields'"

        if required_fields:
            fields = record.get("fields", record)
            for field in required_fields:
                assert field in fields, f"Field '{field}' missing from record"

    return _assert


@pytest.fixture
def assert_valid_table():
    """Helper to assert a table has required structure."""

    def _assert(table: Dict[str, Any]):
        assert "id" in table, "Table must have 'id'"
        # Optional: assert "label" in table

    return _assert


@pytest.fixture
def assert_valid_column():
    """Helper to assert a column has required structure."""

    def _assert(column: Dict[str, Any]):
        assert "id" in column, "Column must have 'id'"
        assert "fields" in column, "Column must have 'fields'"
        assert "type" in column["fields"], "Column fields must have 'type'"

    return _assert
