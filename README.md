# Grist AI Assistant

An AI-powered assistant for Grist documents using LangChain and OpenAI function calling.

## Overview

This project provides a custom widget backend for Grist that allows users to interact with their documents using natural language. The assistant can query data, modify records, create tables, and perform various document operations through conversational AI.

### Key Features

- Natural language interface for Grist documents
- OpenAI function calling for precise tool execution
- LangChain agent for orchestration
- Mock Grist service for Phase 1 testing
- FastAPI backend with async support
- Docker-based deployment
- Colorful, visual logging

### Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **LLM Framework**: LangChain (without LangGraph)
- **LLM Provider**: Any OpenAI-compatible API (OpenAI, HuggingFace, Ollama, etc.)
- **Database**: PostgreSQL (optional, for conversation history)
- **Cache**: Redis (optional, for caching)
- **Infrastructure**: Docker + docker-compose

## Project Status

**Current Phase**: Phase 1 - Foundation

This is a working prototype with:
- ✅ Core LLM integration
- ✅ 5 essential tools (get_tables, get_table_columns, query_document, add_records, update_records)
- ✅ Basic agent with function calling
- ✅ FastAPI /chat endpoint
- ✅ Mock Grist service for testing

**Coming Next** (Phase 2):
- Validation layer (permissions, schema, types)
- Error handling improvements
- Preview system for destructive operations
- Transaction management
- Complete tool implementation

## Project Structure

```
grist-api-v2/
├── app/
│   ├── core/              # Core AI components
│   │   ├── llm.py         # LLM configuration
│   │   ├── prompts.py     # System prompts
│   │   ├── tools.py       # Grist tools (5 implemented)
│   │   └── agent.py       # Main agent
│   ├── services/          # Business logic
│   │   └── grist_service.py  # Mock Grist interface
│   ├── api/               # FastAPI routes
│   │   ├── main.py        # FastAPI app
│   │   ├── routes.py      # Route handlers
│   │   └── models.py      # Pydantic models
│   ├── middleware/        # (Phase 2)
│   └── models/            # (Phase 2)
├── tests/                 # (Phase 5)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Docker and docker-compose
- OpenAI API key
- Python 3.11+ (for local development)

### Setup

1. **Clone the repository**

```bash
cd grist-api-v2
```

2. **Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

3. **Start services with Docker Compose**

```bash
docker-compose up --build
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- API server (port 8000)

4. **Verify the service is running**

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Local Development (without Docker)

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Start PostgreSQL and Redis**

```bash
docker-compose up postgres redis
```

3. **Run the API server**

```bash
python -m uvicorn app.api.main:app --reload
```

## API Usage

### Chat Endpoint

**POST** `/api/v1/chat`

Send a message to the AI assistant.

**Request Body**:

```json
{
  "message": "What tables are in this document?",
  "chat_history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you today?"
    }
  ],
  "current_page_name": "data",
  "current_page_id": 1
}
```

**Response**:

```json
{
  "response": "This document has 2 tables: Table1 and Projects.",
  "success": true,
  "tool_calls": [
    {
      "tool_name": "get_tables",
      "tool_input": {},
      "tool_output": [
        {"id": "Table1", "label": "Table 1"},
        {"id": "Projects", "label": "Projects"}
      ]
    }
  ]
}
```

### Example Queries

**Query data**:
```json
{
  "message": "Show me all active projects"
}
```

**Add records**:
```json
{
  "message": "Add a new project called 'Q4 Launch' with budget 50000"
}
```

**Update records**:
```json
{
  "message": "Update project 'Q4 Launch' to status 'In Progress'"
}
```

## Testing with curl

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Ask about tables
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What tables are in this document?"
  }'

# Query data
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me all projects"
  }'
```

## Development

### Running Tests (Phase 5)

```bash
pytest
pytest --cov=app tests/
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
ruff app/ tests/

# Type check
mypy app/
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Architecture

### Agent Flow

1. User sends message to `/api/v1/chat`
2. FastAPI creates `GristAgent` with context
3. Agent uses LangChain with OpenAI function calling
4. LLM decides which tools to call
5. Tools interact with `GristService` (mock or real)
6. Agent returns formatted response

### Tools (Phase 1)

- `get_tables()` - List all tables
- `get_table_columns(table_id)` - Get columns for a table
- `query_document(query, args)` - Execute SQL query
- `add_records(table_id, records)` - Add new records
- `update_records(table_id, record_ids, records)` - Update existing records

## Roadmap

See the project description for the complete 5-phase roadmap:

- ✅ **Phase 1**: Foundation (Current)
- ⏳ **Phase 2**: Robustness (Error handling, validation)
- ⏳ **Phase 3**: Intelligence (Context management, smart suggestions)
- ⏳ **Phase 4**: Monitoring (LLM tracing, metrics)
- ⏳ **Phase 5**: Testing & Polish (Tests, docs, optimization)

## Configuration

### Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `OPENAI_API_KEY` - OpenAI API key (required)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Logging

The application uses colorful console logging with:
- **GREEN** - Info messages
- **CYAN** - Debug messages
- **YELLOW** - Warnings
- **RED** - Errors

Example output:
```
INFO     app.api.main 🚀 Starting Grist AI Assistant API...
INFO     app.core.agent GristAgent initialized with 5 tools
INFO     app.api.routes Received chat request: What tables are in this...
DEBUG    app.services.grist_service Found 2 tables
INFO     app.api.routes Chat request completed successfully, made 1 tool calls
```

## Troubleshooting

### API returns 500 error

Check that:
1. OpenAI API key is set correctly in `.env`
2. PostgreSQL and Redis are running
3. Check logs: `docker-compose logs api`

### Agent timeout

- Increase `timeout` in `app/core/llm.py`
- Reduce `max_iterations` in `app/core/agent.py`

### Docker build fails

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Contributing

This is currently in active development (Phase 1). Once Phase 2 is complete, we'll open up for contributions.

## License

[To be determined]

## Contact

[Project maintainer contact info]

---

**Built with**: LangChain, FastAPI, Docker
**Compatible with**: Any OpenAI-compatible LLM API
**Current Version**: 0.1.0 (Phase 1 - Foundation)
