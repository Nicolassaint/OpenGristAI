# Changelog

All notable changes to OpenGristAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Function calling diagnostics system** for LLM compatibility testing
- **Detailed logging** for tool calls, responses, and execution flow
- **Execution metrics** (iterations, tool calls, failure rates) in agent responses
- **Automatic validation** for function calling support at agent startup (optional)
- `validate_function_calling()` method to test LLM compatibility
- **Pattern detection** for common failure modes (no tools, empty lists, high failure rates)
- **Diagnostic warnings** when LLM behavior is suspicious
- Test script for validating new models (`tests/test_function_calling_validation.py`)
- Comprehensive documentation (`docs/FUNCTION_CALLING_DIAGNOSTICS.md`)
- Phase 3: Conversation history with Redis
- Phase 3: Context management across multiple messages
- Phase 4: LangSmith/LangFuse integration for observability

### Changed
- **Enhanced logging** with emojis and severity indicators (✅ ⚠️ ❌ 🔴)
- Agent now returns `metrics` in response payload
- Improved error messages with actionable recommendations

### Fixed
- Silent failures when LLM doesn't support function calling
- Difficult-to-diagnose compatibility issues with different model providers

## [0.2.0] - 2025-01-19

### Added
- **Confirmation system** for destructive operations
- **13 Grist tools** via official REST API (was 5)
- `get_sample_records` tool for inspecting actual data values
- `add_table`, `add_table_column`, `update_table_column`, `remove_table_column` tools
- `remove_records` tool with automatic confirmation
- **Validation layer** for tables, columns, and data
- **Preview service** for showing operation impacts before execution
- **Confirmation service** with TTL and in-memory storage
- Multi-authentication support (JWT token + API key)
- Comprehensive error handling and middleware
- Full test suite (unit + integration tests)

### Changed
- Renamed project to **OpenGristAI**
- Made project open source with MIT license
- Improved README with branding and clearer structure
- Enhanced `.env.example` with better organization
- Updated prompts to French for DINUM instance
- Agent now uses centralized Pydantic Settings for configuration
- HTTP client authentication via query parameter (not header)

### Fixed
- Agent execution loop now properly tracks `intermediate_steps`
- Proper cleanup of HTTP connections
- Better error messages for validation failures

## [0.1.0] - 2024-12-15

### Added
- Initial release
- Custom agent execution loop (replacing AgentExecutor)
- 5 core tools: `get_tables`, `get_table_columns`, `query_document`, `add_records`, `update_records`
- LangChain integration with OpenAI function calling
- FastAPI backend with async support
- Docker + docker-compose deployment
- Colorful structured logging
- Support for any OpenAI-compatible API

---

**Legend**:
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes

