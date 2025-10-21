"""
LLM Configuration Module

This module handles the initialization and configuration of the LangChain LLM.
Supports OpenAI-compatible APIs (OpenAI, Ollama, LM Studio, etc.)
Includes validation and diagnostics for function calling compatibility.
"""

import logging
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from app.models import settings

logger = logging.getLogger(__name__)


class LLMConfig:
    """Configuration for the LLM."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        # Get configuration from centralized settings
        # Allow overrides via parameters, but default to settings
        self.api_key = settings.openai_api_key
        self.base_url = base_url if base_url is not None else settings.openai_base_url
        self.model_name = model_name or settings.openai_model

        self.temperature = (
            temperature if temperature is not None else settings.llm_temperature
        )
        self.max_tokens = (
            max_tokens if max_tokens is not None else settings.llm_max_tokens
        )
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries or settings.llm_max_retries

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. " "Please set it in your .env file."
            )


async def validate_function_calling(
    llm: BaseChatModel, model_name: str
) -> Dict[str, Any]:
    """
    Validates that the LLM properly supports function calling.

    This performs a simple test call with a dummy tool to verify:
    1. The model understands tool binding
    2. The model can generate tool calls in the correct format
    3. The response structure is as expected

    Args:
        llm: The LLM instance to test
        model_name: Name of the model (for logging)

    Returns:
        Dictionary with validation results:
            - supported: bool - Whether function calling is supported
            - has_tool_calls_attr: bool - Whether response has tool_calls attribute
            - test_passed: bool - Whether the test call succeeded
            - error: Optional error message
            - response_type: Type of response received
    """
    logger.info(f"🔍 Validating function calling support for model: {model_name}")

    # Create a simple test tool
    @tool
    def test_tool(x: int) -> int:
        """A simple test tool that returns x + 1."""
        return x + 1

    try:
        # Bind the test tool
        llm_with_test_tool = llm.bind_tools([test_tool])

        # Make a test call that should trigger the tool
        test_message = HumanMessage(
            content="Call the test_tool function with x=5. This is a test."
        )

        response = await llm_with_test_tool.ainvoke([test_message])

        # Analyze the response
        response_type = type(response).__name__
        has_tool_calls = hasattr(response, "tool_calls")
        tool_calls_value = getattr(response, "tool_calls", None)

        logger.debug(f"Test response type: {response_type}")
        logger.debug(f"Has tool_calls attribute: {has_tool_calls}")
        logger.debug(f"tool_calls value: {tool_calls_value}")

        # Check if function calling is working
        if has_tool_calls and tool_calls_value:
            logger.info(f"✅ Function calling validation PASSED for {model_name}")
            logger.info(
                f"   Model correctly generated {len(tool_calls_value)} tool call(s)"
            )
            return {
                "supported": True,
                "has_tool_calls_attr": True,
                "test_passed": True,
                "response_type": response_type,
                "num_tool_calls": len(tool_calls_value),
            }
        elif has_tool_calls and not tool_calls_value:
            logger.warning(
                f"⚠️  Function calling validation UNCERTAIN for {model_name}: "
                f"Model has tool_calls attribute but returned empty list. "
                f"This may indicate partial support or the model choosing not to call tools."
            )
            return {
                "supported": True,  # Has the attribute
                "has_tool_calls_attr": True,
                "test_passed": False,
                "response_type": response_type,
                "warning": "Empty tool_calls list",
            }
        else:
            logger.error(
                f"🔴 Function calling validation FAILED for {model_name}: "
                f"Model response does not have 'tool_calls' attribute. "
                f"This model likely does not support function calling."
            )
            return {
                "supported": False,
                "has_tool_calls_attr": False,
                "test_passed": False,
                "response_type": response_type,
                "error": "No tool_calls attribute in response",
            }

    except Exception as e:
        logger.error(
            f"❌ Function calling validation ERROR for {model_name}: {str(e)}",
            exc_info=True,
        )
        return {
            "supported": False,
            "has_tool_calls_attr": False,
            "test_passed": False,
            "error": str(e),
            "exception_type": type(e).__name__,
        }


def get_llm(config: Optional[LLMConfig] = None) -> BaseChatModel:
    """
    Initialize and return a configured LLM instance.

    Supports any OpenAI-compatible API through centralized configuration.
    See app/config.py for available settings.

    Args:
        config: Optional LLMConfig for custom configuration.
                If not provided, uses settings from app.config.

    Returns:
        Configured ChatOpenAI instance with function calling support.

    Example:
        # Use default configuration from app.config
        llm = get_llm()

        # Or override specific settings
        custom_config = LLMConfig(temperature=0.7)
        llm = get_llm(custom_config)

    TODO:
        - Add support for streaming responses
        - Implement token usage tracking
        - Add retry logic with exponential backoff
        - Consider caching for repeated queries
    """
    if config is None:
        config = LLMConfig()

    # Build kwargs for ChatOpenAI
    kwargs = {
        "model": config.model_name,
        "temperature": config.temperature,
        "timeout": config.timeout,
        "max_retries": config.max_retries,
        "api_key": config.api_key,
    }

    # Add base_url if provided (for OpenAI-compatible servers)
    if config.base_url:
        kwargs["base_url"] = config.base_url
        logger.info(f"Using OpenAI-compatible API at: {config.base_url}")

    if config.max_tokens:
        kwargs["max_tokens"] = config.max_tokens

    logger.info(f"Initializing LLM: model={config.model_name}")

    llm = ChatOpenAI(**kwargs)

    return llm


# TODO: Add LLM monitoring/observability
# - Track token usage per request
# - Track latency metrics
# - Log all LLM calls with context
# - Integrate with LangSmith or LangFuse for tracing

# TODO: Add error handling
# - Handle rate limiting (429 errors)
# - Handle context length errors
# - Handle API timeouts gracefully
# - Implement circuit breaker pattern

# TODO: Add cost optimization
# - Implement prompt caching where appropriate
# - Consider using cheaper models for simple queries
# - Add token usage warnings for expensive calls
