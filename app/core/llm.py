"""
LLM Configuration Module

This module handles the initialization and configuration of the LangChain LLM.
Supports OpenAI-compatible APIs (OpenAI, Ollama, LM Studio, etc.)
"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from app.config import settings

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

        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries or settings.llm_max_retries

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. "
                "Please set it in your .env file."
            )


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
