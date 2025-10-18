# Contributing to Grist AI Assistant

Thank you for your interest in contributing to the Grist AI Assistant! This document provides guidelines and best practices for contributing to this project.

## Table of Contents

- [Project Philosophy](#project-philosophy)
- [Development Setup](#development-setup)
- [Code Organization](#code-organization)
- [Configuration Management](#configuration-management)
- [Code Style Guidelines](#code-style-guidelines)
- [Adding New Tools](#adding-new-tools)
- [Testing Requirements](#testing-requirements)
- [Commit Message Conventions](#commit-message-conventions)
- [Pull Request Process](#pull-request-process)

## Project Philosophy

This project follows these core principles:

1. **Generic and Agnostic**: The codebase must remain model-agnostic and provider-agnostic. No hardcoded references to specific LLM providers or models.

2. **Centralized Configuration**: All configuration must use the centralized `app/config.py` module. Never use `os.getenv()` directly in the codebase.

3. **Type Safety**: All code must use Python type hints for better IDE support and error detection.

4. **Clean and Maintainable**: Code should be self-documenting with clear naming conventions and minimal comments. When comments are needed, they should explain "why", not "what".

5. **Step-by-Step Approach**: Build solid foundations before adding new features. Quality over quantity.

## Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd grist-api-v2
```

2. Create and activate a conda environment:
```bash
conda create -n grist python=3.11
conda activate grist
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure your environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the development server:
```bash
python -m app.api.main
```

## Code Organization

```
grist-api-v2/
├── app/
│   ├── config.py           # ⚠️ CENTRALIZED CONFIGURATION - Use this!
│   ├── core/               # Core business logic
│   │   ├── agent.py        # Main agent orchestration
│   │   ├── llm.py          # LLM initialization
│   │   ├── prompts.py      # System prompts
│   │   └── tools.py        # Tool definitions
│   ├── services/           # External service integrations
│   │   ├── grist_client.py # Grist API HTTP client
│   │   └── grist_service.py # Grist business logic
│   ├── api/                # FastAPI application
│   │   ├── main.py         # Application entry point
│   │   ├── routes.py       # API endpoints
│   │   └── models.py       # Pydantic request/response models
│   └── middleware/         # FastAPI middleware
│       └── error_handler.py
└── tests/
    ├── unit/               # Unit tests
    └── integration/        # Integration tests
```

## Configuration Management

**⚠️ CRITICAL: Never use `os.getenv()` directly in your code!**

### ✅ CORRECT - Use centralized configuration:

```python
from app.config import settings

def my_function():
    model_name = settings.openai_model
    base_url = settings.grist_base_url
    max_iterations = settings.agent_max_iterations
```

### ❌ INCORRECT - Direct environment variable access:

```python
import os

def my_function():
    model_name = os.getenv("OPENAI_MODEL")  # DON'T DO THIS!
    base_url = os.getenv("GRIST_BASE_URL")   # DON'T DO THIS!
```

### Adding New Configuration Variables

1. Add the variable to `app/config.py` in the appropriate section:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    my_new_setting: str = "default_value"
    """Clear description of what this setting does"""
```

2. Add the variable to `.env.example` with documentation:

```bash
# My Feature Configuration
MY_NEW_SETTING=example_value
```

3. Update your `.env` file locally for development

## Code Style Guidelines

### General Principles

1. **Type Hints**: All functions must have type hints for parameters and return values
2. **Docstrings**: Use Google-style docstrings for modules, classes, and public functions
3. **Naming Conventions**:
   - Classes: `PascalCase` (e.g., `GristAgent`, `ToolCall`)
   - Functions/methods: `snake_case` (e.g., `get_llm`, `query_document`)
   - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
   - Private methods: prefix with `_` (e.g., `_build_url`, `_validate_input`)

### Type Hints Example

```python
from typing import Optional, List, Dict, Any

async def process_query(
    query: str,
    document_id: str,
    options: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Process a SQL query against a Grist document.

    Args:
        query: SQL query string to execute
        document_id: ID of the Grist document
        options: Optional query execution options

    Returns:
        List of query result rows as dictionaries

    Raises:
        ValueError: If query is empty or invalid
        GristAPIError: If API call fails
    """
    # Implementation...
```

### Docstring Example

```python
def get_table_columns(table_id: str) -> List[ColumnInfo]:
    """
    Retrieve column information for a specific table.

    This function fetches metadata about all columns in a table, including:
    - Column ID and label
    - Data type
    - Formula (if any)

    Args:
        table_id: The ID of the table to query

    Returns:
        List of ColumnInfo objects with metadata for each column

    Example:
        >>> columns = get_table_columns("Students")
        >>> for col in columns:
        ...     print(f"{col.label}: {col.type}")
    """
    # Implementation...
```

### Model-Agnostic Code

**❌ AVOID** model-specific references:

```python
# Don't do this:
model = "gpt-4o-mini"  # Hardcoded model name
# This is specifically optimized for GPT-4
# Works better with Claude
```

**✅ PREFER** generic, configurable code:

```python
from app.config import settings

model = settings.openai_model  # Uses configured model
# This implementation works with any OpenAI-compatible model
# Temperature can be adjusted via OPENAI_TEMPERATURE env var
```

## Adding New Tools

Tools are LangChain functions that the agent can call. To add a new tool:

### 1. Define the Tool Function

Create your tool in `app/core/tools.py`:

```python
from langchain.tools import tool
from typing import Dict, Any

@tool
async def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of what the tool does.

    This description is shown to the LLM, so be clear and concise.
    Explain when the tool should be used and what it returns.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Dictionary with the tool's results
    """
    # Get Grist service from context
    grist_service = _get_grist_service()

    # Implement your tool logic
    result = await grist_service.some_operation(param1, param2)

    return {"success": True, "data": result}
```

### 2. Register the Tool

Add your tool to the `get_all_tools()` function in `app/core/tools.py`:

```python
def get_all_tools() -> List[BaseTool]:
    """Get all available tools for the agent."""
    return [
        # Existing tools...
        get_tables,
        query_document,

        # Your new tool
        my_new_tool,
    ]
```

### 3. Implement Service Layer (if needed)

If your tool needs to interact with Grist API, add methods to `app/services/grist_service.py`:

```python
async def some_operation(self, param1: str, param2: int) -> Dict[str, Any]:
    """
    Implement the actual API interaction.

    Args:
        param1: First parameter
        param2: Second parameter

    Returns:
        API response data
    """
    # Use the Grist client to make API calls
    response = await self.client.request(
        method="GET",
        endpoint=f"/tables/{param1}/operation",
        params={"value": param2},
    )
    return response
```

### 4. Add Tests

Create unit tests in `tests/unit/test_tools.py`:

```python
import pytest
from app.core.tools import my_new_tool

@pytest.mark.asyncio
async def test_my_new_tool():
    """Test that my_new_tool works correctly."""
    result = await my_new_tool(param1="test", param2=42)

    assert result["success"] is True
    assert "data" in result
```

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_tools.py

# Run specific test
pytest tests/unit/test_tools.py::test_my_new_tool
```

### Writing Tests

1. **Unit Tests**: Test individual functions in isolation
   - Mock external dependencies (Grist API, LLM calls)
   - Test edge cases and error handling
   - Place in `tests/unit/`

2. **Integration Tests**: Test complete workflows
   - Test agent execution end-to-end
   - Test API endpoints
   - Place in `tests/integration/`

### Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.grist_service import GristService

@pytest.mark.asyncio
async def test_get_table_columns():
    """Test that get_table_columns returns correct structure."""
    # Arrange
    mock_response = {
        "columns": [
            {"id": "A", "label": "Name", "type": "Text"},
            {"id": "B", "label": "Age", "type": "Int"},
        ]
    }

    with patch("app.services.grist_client.GristClient.request") as mock_request:
        mock_request.return_value = mock_response

        service = GristService(
            document_id="test_doc",
            access_token="test_token",
        )

        # Act
        result = await service.get_table_columns("Students")

        # Assert
        assert len(result) == 2
        assert result[0]["label"] == "Name"
        assert result[1]["type"] == "Int"
```

## Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change or bug fix)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build, etc.)

### Examples

```bash
feat(tools): add get_table_columns tool

Implement new tool to retrieve column metadata for Grist tables.
This allows the agent to understand table structure before queries.

Closes #42

---

fix(auth): use query parameter for Grist widget tokens

Widget tokens must be passed as ?auth=TOKEN, not Authorization header.

---

docs(contributing): add guidelines for adding new tools

---

refactor(config): centralize environment variable management

Replace all os.getenv() calls with settings from app/config.py
```

## Pull Request Process

1. **Create a Branch**:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make Your Changes**: Follow the guidelines in this document

3. **Test Your Changes**:
   ```bash
   pytest
   ```

4. **Commit Your Changes**: Use conventional commit messages

5. **Push Your Branch**:
   ```bash
   git push origin feat/my-feature
   ```

6. **Create Pull Request**:
   - Provide a clear title and description
   - Reference any related issues
   - Ensure all CI checks pass

7. **Code Review**:
   - Address review comments
   - Keep the PR focused and small when possible

8. **Merge**: Once approved, your PR will be merged

## Questions?

If you have questions about contributing, please:

1. Check the [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details
2. Review existing code for examples
3. Open an issue for discussion

Thank you for contributing to Grist AI Assistant!
