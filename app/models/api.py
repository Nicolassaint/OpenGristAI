"""
API Request/Response Models

Pydantic models for request and response validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UIMessage(BaseModel):
    """A single message in the conversation (UI format)."""

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    parts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Message parts"
    )
    content: Optional[str] = Field(default=None, description="Message content (legacy)")
    createdAt: Optional[Any] = Field(default=None, description="Creation timestamp")
    experimental_attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Attachments"
    )


class ChatRequest(BaseModel):
    """Request body for the chat endpoint (from Grist front-end)."""

    messages: List[UIMessage] = Field(..., description="Conversation messages")
    documentId: str = Field(..., description="Grist document ID/name")
    currentTableId: Optional[str] = Field(
        default=None, description="ID of the table currently being viewed by the user"
    )
    currentTableName: Optional[str] = Field(
        default=None,
        description="Human-readable name of the table currently being viewed",
    )
    executionMode: Optional[str] = Field(default=None, description="Execution mode")
    webhookUrl: Optional[str] = Field(default=None, description="Webhook URL")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": "What tables are in this document?",
                            }
                        ],
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ],
                "documentId": "my-document",
                "currentTableId": "Clients",
                "currentTableName": "Clients",
                "executionMode": "production",
            }
        }


class ToolCall(BaseModel):
    """Information about a tool call made by the agent."""

    tool_name: str = Field(..., description="Name of the tool called")
    tool_input: Dict[str, Any] = Field(..., description="Input arguments to the tool")
    tool_output: Any = Field(..., description="Output from the tool")


class ChatResponse(BaseModel):
    """Response body for the chat endpoint (for Grist front-end)."""

    response: Optional[str] = Field(None, description="Assistant's response text")
    sql_query: Optional[str] = Field(
        default=None, description="SQL query executed (if any)"
    )
    agent_used: Optional[str] = Field(
        default=None, description="Agent/model used for this response"
    )
    data_analyzed: Optional[Any] = Field(
        default=None, description="Data analyzed during execution"
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        default=None, description="List of tools called during execution"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    requires_confirmation: Optional[bool] = Field(
        default=False, description="Whether user confirmation is required"
    )
    confirmation_request: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Confirmation request details if confirmation required",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "This document has 2 tables: Table1 and Projects.",
                "sql_query": "SELECT * FROM sqlite_master WHERE type='table'",
                "agent_used": "model-name",
                "tool_calls": [
                    {
                        "tool_name": "get_tables",
                        "tool_input": {},
                        "tool_output": [
                            {"id": "Table1", "label": "Table 1"},
                            {"id": "Projects", "label": "Projects"},
                        ],
                    }
                ],
            }
        }


class HealthResponse(BaseModel):
    """Response for health check endpoint."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
