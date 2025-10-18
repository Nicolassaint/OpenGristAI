# Architecture Documentation

This document describes the technical architecture of the Grist AI Assistant project.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Module Breakdown](#module-breakdown)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Configuration Management](#configuration-management)
- [Agent Execution Loop](#agent-execution-loop)
- [Extension Points](#extension-points)
- [Technology Stack](#technology-stack)

## Overview

The Grist AI Assistant is an AI-powered assistant that helps users interact with Grist documents through natural language. It uses LangChain to orchestrate an LLM with custom tools that interact with the Grist API.

### Key Features

- Natural language interface to Grist documents
- SQL query generation and execution
- Table, column, and data management
- OpenAI-compatible API support (works with any provider)
- Custom agent execution loop for reliable tool calling
- Type-safe configuration management

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Grist Widget (Frontend)                   │
│  - Sends user messages with document context                    │
│  - Receives AI responses                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /chat
                             │ (document_id, token, message)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application (Backend)                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              API Layer (app/api/)                        │   │
│  │  - routes.py: Endpoint handlers                          │   │
│  │  - models.py: Request/response validation                │   │
│  │  - main.py: Application setup                            │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │            Core Layer (app/core/)                        │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │         GristAgent (agent.py)                   │    │   │
│  │  │  - Orchestrates LLM and tools                   │    │   │
│  │  │  - Custom execution loop                        │    │   │
│  │  │  - Manages conversation history                 │    │   │
│  │  └────────┬────────────────────────┬────────────────┘    │   │
│  │           │                        │                     │   │
│  │  ┌────────▼─────────┐   ┌─────────▼─────────┐          │   │
│  │  │  LLM (llm.py)    │   │  Tools (tools.py) │          │   │
│  │  │  - ChatOpenAI    │   │  - @tool functions│          │   │
│  │  │  - bind_tools()  │   │  - Grist operations          │   │
│  │  └──────────────────┘   └─────────┬─────────┘          │   │
│  └──────────────────────────────────┼─────────────────────┘   │
│                                      │                          │
│  ┌──────────────────────────────────▼─────────────────────┐   │
│  │        Service Layer (app/services/)                    │   │
│  │  ┌───────────────────────────────────────────────┐     │   │
│  │  │      GristService (grist_service.py)          │     │   │
│  │  │  - Business logic for Grist operations        │     │   │
│  │  └───────────────────┬───────────────────────────┘     │   │
│  │                      │                                  │   │
│  │  ┌───────────────────▼───────────────────────────┐     │   │
│  │  │      GristClient (grist_client.py)            │     │   │
│  │  │  - HTTP client for Grist API                  │     │   │
│  │  │  - Query parameter auth (?auth=TOKEN)         │     │   │
│  │  └───────────────────────────────────────────────┘     │   │
│  └─────────────────────────┬───────────────────────────────┘   │
└────────────────────────────┼───────────────────────────────────┘
                             │
                             │ HTTPS API Calls
                             │ ?auth=TOKEN
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Grist Instance (External)                     │
│  - grist.numerique.gouv.fr (DINUM)                              │
│  - docs.getgrist.com (official)                                  │
│  - Self-hosted instances                                         │
└─────────────────────────────────────────────────────────────────┘

                             ┌───────────────────┐
                             │  LLM Provider     │
                             │  (External)       │
                             │                   │
                             │  - OpenAI         │
                             │  - HuggingFace    │
                             │  - Ollama (local) │
                             │  - Any compatible │
                             └───────────────────┘
```

## Module Breakdown

### `app/config.py` - Configuration Management

**Purpose**: Centralized, type-safe configuration using Pydantic Settings.

**Key Classes**:
- `Settings`: Pydantic model that loads and validates environment variables
- `settings`: Global singleton instance

**Usage**:
```python
from app.config import settings

model_name = settings.openai_model  # Type-safe access
base_url = settings.grist_base_url
```

**Environment Variables**:
- Application: `ENVIRONMENT`, `LOG_LEVEL`, `API_HOST`, `API_PORT`
- LLM: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`
- Grist: `GRIST_BASE_URL`
- Agent: `AGENT_MAX_ITERATIONS`, `AGENT_VERBOSE`

### `app/core/` - Core Business Logic

#### `agent.py` - Agent Orchestration

**Purpose**: Main orchestrator that runs the agent execution loop.

**Key Class**: `GristAgent`

**Responsibilities**:
- Initialize LLM with tools bound
- Manage conversation history
- Execute custom agent loop
- Handle tool calls and responses

**Why Custom Loop?**: LangChain's `AgentExecutor` had issues with some OpenAI-compatible models (returning empty `intermediate_steps`). Our custom loop provides:
- Full control over execution
- Better debugging visibility
- Support for any OpenAI-compatible model

**Agent Loop Steps**:
1. Build messages (system prompt + history + user message)
2. Call LLM with tools bound
3. Check if LLM wants to call tools
4. Execute tools in sequence
5. Add tool results to conversation
6. Repeat until LLM provides final answer

#### `llm.py` - LLM Configuration

**Purpose**: Initialize and configure the LLM instance.

**Key Functions**:
- `get_llm()`: Returns configured `ChatOpenAI` instance
- `LLMConfig`: Configuration dataclass

**Supports**:
- OpenAI official API
- OpenAI-compatible APIs (HuggingFace, Ollama, LM Studio, etc.)
- Any provider with OpenAI-compatible `/v1/chat/completions` endpoint

#### `tools.py` - Tool Definitions

**Purpose**: Define tools that the agent can use.

**Pattern**: Use LangChain's `@tool` decorator:

```python
from langchain.tools import tool

@tool
async def my_tool(param: str) -> dict:
    """
    Description shown to the LLM.
    Explain what the tool does and when to use it.
    """
    # Get service from context
    grist_service = _get_grist_service()

    # Execute operation
    result = await grist_service.operation(param)

    return {"success": True, "data": result}
```

**Tool Context**: Tools access `GristService` via a context variable set by the agent.

#### `prompts.py` - System Prompts

**Purpose**: Define system prompts that guide the agent's behavior.

**Key Prompts**:
- Instructions for Grist operations
- Tool usage guidelines
- Response formatting rules

### `app/services/` - External Service Integration

#### `grist_service.py` - Business Logic

**Purpose**: High-level business logic for Grist operations.

**Responsibilities**:
- Validate inputs
- Coordinate multiple API calls
- Transform data structures
- Handle errors gracefully

**Example**:
```python
async def get_table_with_columns(self, table_id: str) -> dict:
    """Get table info AND its columns in one operation."""
    # Coordinate multiple API calls
    table = await self.get_table(table_id)
    columns = await self.get_table_columns(table_id)

    return {
        "table": table,
        "columns": columns,
    }
```

#### `grist_client.py` - HTTP Client

**Purpose**: Low-level HTTP client for Grist API.

**Key Implementation Details**:
- Uses `httpx.AsyncClient` for async HTTP
- Authentication via query parameter: `?auth=TOKEN`
  - **Not** `Authorization: Bearer` header (widget tokens don't support this)
- Automatic URL building with auth token
- Connection pooling and timeout management

**Authentication Flow**:
```python
def _build_url(self, path: str) -> str:
    """Build URL with auth query parameter."""
    url = urljoin(self.base_url, path)
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}auth={self.access_token}"
```

### `app/api/` - API Layer

#### `main.py` - Application Setup

**Purpose**: FastAPI application initialization and configuration.

**Components**:
- Logging configuration (colorlog)
- CORS middleware
- Lifespan management (startup/shutdown)
- Exception handlers

#### `routes.py` - Endpoints

**Purpose**: Define HTTP endpoints.

**Main Endpoint**: `POST /chat`

**Request**:
```json
{
  "message": "Show me all students",
  "document_id": "abc123",
  "grist_token": "jwt_token_here",
  "current_page_name": "Students",
  "current_page_id": 1,
  "chat_history": []
}
```

**Response**:
```json
{
  "response": "Here are the students...",
  "sql_query": "SELECT * FROM Students",
  "tool_calls": [
    {
      "tool_name": "query_document",
      "tool_input": {"query": "SELECT * FROM Students"},
      "tool_output": [{"id": 1, "name": "Alice"}]
    }
  ]
}
```

#### `models.py` - Request/Response Models

**Purpose**: Pydantic models for API validation.

**Benefits**:
- Automatic request validation
- Type safety
- Auto-generated OpenAPI docs
- Clear API contracts

## Data Flow

### Chat Request Flow

```
1. Frontend sends POST /chat
   ├─ message: "Show me all students"
   ├─ document_id: "abc123"
   ├─ grist_token: "eyJ..."
   └─ current_page_name: "Students"

2. API validates request (models.py)
   └─ Pydantic validates all fields

3. Create GristAgent instance
   ├─ Initialize GristService with token + document_id
   ├─ Initialize LLM from config (settings.openai_model)
   ├─ Bind tools to LLM
   └─ Generate system prompt with context

4. Agent.run() - Custom execution loop
   │
   ├─ Build messages: [SystemMessage, HumanMessage]
   │
   ├─ Iteration 1:
   │  ├─ Call LLM with tools bound
   │  ├─ LLM responds with tool_calls: [get_tables]
   │  ├─ Execute get_tables → Returns ["Students", "Teachers"]
   │  └─ Add ToolMessage to conversation
   │
   ├─ Iteration 2:
   │  ├─ Call LLM with updated conversation
   │  ├─ LLM responds with tool_calls: [query_document]
   │  ├─ Execute query_document("SELECT * FROM Students")
   │  └─ Add ToolMessage with query results
   │
   └─ Iteration 3:
      ├─ Call LLM with query results
      ├─ LLM responds with NO tool_calls (final answer)
      └─ Return {"output": "Here are the students...", "intermediate_steps": [...]}

5. API formats response
   ├─ Extract SQL query from intermediate_steps
   ├─ Format tool_calls for frontend
   └─ Return ChatResponse

6. Frontend displays response to user
```

### Tool Execution Flow

```
1. LLM decides to call a tool
   tool_call = {
     "name": "query_document",
     "args": {"query": "SELECT * FROM Students"}
   }

2. Agent executes tool
   tool = tools_by_name["query_document"]
   result = await tool.ainvoke(args)

3. Tool function runs (@tool decorator)
   async def query_document(query: str) -> dict:
       grist_service = _get_grist_service()  # Get from context
       return await grist_service.query_document(query)

4. GristService processes request
   async def query_document(self, query: str) -> dict:
       # Validate query
       # Call Grist client
       return await self.client.execute_query(query)

5. GristClient makes HTTP request
   url = self._build_url(f"/docs/{doc_id}/sql")
   response = await self.client.post(url, json={"query": query})

6. Result bubbles back up
   GristClient → GristService → Tool → Agent → ToolMessage
```

## Design Patterns

### 1. Dependency Injection

**Pattern**: Pass dependencies through constructors, not global state.

```python
class GristAgent:
    def __init__(self, document_id: str, grist_token: str, ...):
        # Dependencies injected
        self.grist_service = GristService(
            document_id=document_id,
            access_token=grist_token,
        )
```

### 2. Settings Pattern (Pydantic Settings)

**Pattern**: Centralized configuration with validation.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str  # Required
    openai_model: str = "gpt-4o-mini"  # With default

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()  # Singleton
```

### 3. Context Variable (Tool Access to Services)

**Pattern**: Use context variables to share state without global variables.

```python
from contextvars import ContextVar

_grist_service_context: ContextVar[Optional[GristService]] = ContextVar(
    "grist_service", default=None
)

def set_grist_service(service: GristService):
    _grist_service_context.set(service)

def _get_grist_service() -> GristService:
    return _grist_service_context.get()
```

### 4. Repository Pattern (Service Layer)

**Pattern**: Separate business logic (GristService) from data access (GristClient).

- **GristClient**: Low-level HTTP operations
- **GristService**: High-level business operations

### 5. Custom Agent Loop (Strategy Pattern)

**Pattern**: Custom implementation of agent execution instead of framework defaults.

**Why**: Framework's `AgentExecutor` had limitations with certain models.

**Benefits**:
- Full control over execution
- Better error handling
- Support for all OpenAI-compatible models

## Configuration Management

### Centralized Configuration (app/config.py)

All configuration is managed through `app/config.py` using Pydantic Settings.

**Principles**:
1. ✅ **Single source of truth**: All config in one place
2. ✅ **Type safety**: Pydantic validates types
3. ✅ **Documentation**: Each setting has a docstring
4. ✅ **Defaults**: Sensible defaults where appropriate
5. ✅ **Validation**: Automatic on startup

**Never do this**:
```python
import os
value = os.getenv("SOME_VAR")  # ❌ Don't access env vars directly
```

**Always do this**:
```python
from app.config import settings
value = settings.some_var  # ✅ Use centralized config
```

### Configuration Sections

1. **Application Settings**: Environment, logging, host, port
2. **LLM Provider Settings**: API key, base URL, model, temperature
3. **Grist Settings**: Base URL for Grist instance
4. **Database/Redis Settings**: For future features
5. **Agent Settings**: Max iterations, verbosity
6. **Security Settings**: API keys, JWT secrets, CORS

## Agent Execution Loop

The agent uses a custom execution loop instead of LangChain's `AgentExecutor`.

### Why Custom Loop?

LangChain's `create_openai_functions_agent` + `AgentExecutor` had issues:
- Returned empty `intermediate_steps` with some models
- Limited control over execution flow
- Harder to debug

### Loop Implementation

```python
async def run(self, user_message: str, chat_history: List[Dict] = None):
    # 1. Build conversation
    messages = [SystemMessage(content=self.system_prompt)]
    if chat_history:
        for msg in chat_history:
            messages.append(HumanMessage(...) or AIMessage(...))
    messages.append(HumanMessage(content=user_message))

    # 2. Agent loop
    for iteration in range(self.max_iterations):
        # 3. Call LLM with tools bound
        response = await self.llm_with_tools.ainvoke(messages)

        # 4. Check for tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            # 5. Execute each tool
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                result = await self.tools_by_name[tool_name].ainvoke(tool_args)

                # 6. Add result to conversation
                messages.append(ToolMessage(content=str(result), ...))

            # Continue loop
            continue

        else:
            # 7. No tool calls = final answer
            return {
                "output": response.content,
                "intermediate_steps": intermediate_steps,
                "success": True,
            }

    # Max iterations reached
    return {"error": "Max iterations reached"}
```

### Key Benefits

1. **Full control**: We control every step
2. **Better debugging**: Can log at every step
3. **Model agnostic**: Works with any OpenAI-compatible model
4. **Error recovery**: Can implement custom retry logic
5. **Parallel tools**: Can execute tools in parallel (future)

## Extension Points

### Adding New Tools

Tools are the primary extension point. To add a new capability:

1. Define tool in `app/core/tools.py` with `@tool` decorator
2. Implement business logic in `app/services/grist_service.py`
3. Add HTTP methods in `app/services/grist_client.py` if needed
4. Register tool in `get_all_tools()`

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed instructions.

### Adding New LLM Providers

The system supports any OpenAI-compatible API:

1. Set `OPENAI_BASE_URL` to your provider's endpoint
2. Set `OPENAI_API_KEY` to your API key
3. Set `OPENAI_MODEL` to the model name

Examples:
- **OpenAI**: No `BASE_URL` needed, just API key
- **HuggingFace**: `https://router.huggingface.co/v1`
- **Ollama**: `http://localhost:11434/v1`
- **Custom**: Any endpoint implementing OpenAI Chat Completions API

### Adding New Middleware

Add middleware in `app/api/main.py`:

```python
from fastapi import Request

@app.middleware("http")
async def my_middleware(request: Request, call_next):
    # Before request
    response = await call_next(request)
    # After request
    return response
```

## Technology Stack

### Core Technologies

- **Python 3.11+**: Modern Python with type hints
- **FastAPI**: Modern, fast web framework with automatic OpenAPI docs
- **Pydantic**: Data validation and settings management
- **LangChain**: LLM orchestration framework
  - `langchain-core`: Core abstractions (messages, tools)
  - `langchain-openai`: OpenAI integration (works with compatible APIs)
- **httpx**: Modern async HTTP client

### Development Tools

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **colorlog**: Colored logging for better visibility
- **python-dotenv**: Environment variable management

### External Services

- **Grist**: Document/spreadsheet platform
  - Official: docs.getgrist.com
  - DINUM: grist.numerique.gouv.fr
  - Self-hosted instances
- **LLM Provider**: Any OpenAI-compatible API
  - OpenAI
  - HuggingFace
  - Ollama
  - Custom providers

## Future Architecture Considerations

### Planned Improvements

1. **Streaming Support**: Stream LLM responses as they're generated
2. **Conversation Memory**: Persist conversation history (Redis/PostgreSQL)
3. **Caching**: Cache table schemas and common queries (Redis)
4. **Rate Limiting**: Protect API from abuse
5. **Authentication**: API key or JWT-based auth
6. **Observability**: LangSmith/LangFuse integration for tracing
7. **Parallel Tool Execution**: Execute independent tools concurrently

### Scalability Considerations

- **Stateless Design**: Each request is independent (easier to scale horizontally)
- **Async Throughout**: All I/O operations are async
- **Connection Pooling**: httpx manages connection pools
- **Configuration**: Centralized and easy to override per environment

---

**Last Updated**: 2024
**Version**: 0.1.0
