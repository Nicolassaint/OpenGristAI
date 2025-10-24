"""
Grist AI Agent

This module implements the main agent that orchestrates the LLM and tools.
Uses LangChain's LLM and tool binding with a custom execution loop that:
- Properly handles function calling for all OpenAI-compatible models
- Supports parallel tool execution
- Manages conversation history

Note: We use a custom agent loop instead of LangChain's create_openai_functions_agent
because AgentExecutor has issues with some models (returns empty intermediate_steps).
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.models import settings
from app.core.llm import get_llm
from app.core.prompts import get_system_prompt
from app.core.tools import get_all_tools

logger = logging.getLogger(__name__)


class GristAgent:
    """
    Main agent for the Grist AI Assistant.

    Uses LangChain's LLM and tools with a custom execution loop.
    The loop handles function calling, parallel tool execution, and conversation history.
    """

    def __init__(
        self,
        document_id: str,
        grist_token: str,
        current_page_name: str = "data",
        current_page_id: int = 1,
        current_table_id: Optional[str] = None,
        current_table_name: Optional[str] = None,
        base_url: Optional[str] = None,
        max_iterations: Optional[int] = None,
        verbose: Optional[bool] = None,
        enable_confirmations: bool = True,
        validate_function_calling_on_init: bool = False,
    ):
        """
        Initialize the Grist AI Agent.

        Args:
            document_id: Grist document ID or name
            grist_token: JWT access token from Grist widget
            current_page_name: Name of the current page
            current_page_id: ID of the current page
            current_table_id: ID of the table currently being viewed by the user
            current_table_name: Human-readable name of the table currently being viewed
            base_url: Base URL for Grist API (defaults to settings.grist_base_url)
            max_iterations: Maximum number of tool calls allowed (defaults to settings.agent_max_iterations)
            verbose: Whether to log agent actions (defaults to settings.agent_verbose)
            enable_confirmations: Whether to require confirmation for destructive operations (default: True)
            validate_function_calling_on_init: Whether to validate function calling support at startup (default: False)
                Note: This makes a test API call to the LLM, which may add latency and cost.
        """
        self.document_id = document_id
        self.grist_token = grist_token
        # Use centralized settings with optional overrides
        self.base_url = base_url or settings.grist_base_url
        self.current_page_name = current_page_name
        self.current_page_id = current_page_id
        self.current_table_id = current_table_id
        self.current_table_name = current_table_name
        self.max_iterations = max_iterations or settings.agent_max_iterations
        self.verbose = verbose if verbose is not None else settings.agent_verbose
        self.enable_confirmations = enable_confirmations
        self.validate_function_calling_on_init = validate_function_calling_on_init

        # Store validation results
        self.function_calling_validated = False
        self.function_calling_validation_result: Optional[Dict[str, Any]] = None

        # Create Grist service
        from app.services.grist_service import GristService
        from app.core.tools import set_grist_service

        self.grist_service = GristService(
            document_id=document_id,
            access_token=grist_token,
            base_url=self.base_url,
        )

        # Set the service in the context for tools to access
        set_grist_service(self.grist_service)

        # Create confirmation handler
        from app.core.confirmation import ConfirmationHandler, get_confirmation_service

        self.confirmation_handler = ConfirmationHandler(
            grist_service=self.grist_service,
            enabled=enable_confirmations,
        )
        # Use the global confirmation service to ensure consistency with API routes
        self.confirmation_handler.confirmation_service = get_confirmation_service()

        # Initialize LLM
        self.llm = get_llm()

        # Get all available tools
        self.tools = get_all_tools()

        # Create tool lookup
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        # Bind tools to LLM (LangChain function calling)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Get system prompt
        self.system_prompt = get_system_prompt(
            current_page_name=self.current_page_name,
            current_page_id=self.current_page_id,
            current_table_id=self.current_table_id,
            current_table_name=self.current_table_name,
        )

        logger.info(
            f"GristAgent initialized for document '{document_id}', "
            f"{len(self.tools)} tools, max_iterations={max_iterations}, "
            f"base_url={self.base_url}"
        )

    async def validate_function_calling(self) -> Dict[str, Any]:
        """
        Validates that the configured LLM properly supports function calling.

        This is useful when trying a new model or provider to ensure compatibility
        before experiencing mysterious failures in production.

        Returns:
            Dictionary with validation results (see llm.validate_function_calling)
        """
        from app.core.llm import validate_function_calling

        logger.info("Running function calling validation...")
        result = await validate_function_calling(self.llm, settings.openai_model)

        self.function_calling_validated = True
        self.function_calling_validation_result = result

        # Raise a warning if validation failed
        if not result.get("test_passed", False):
            logger.warning(
                "⚠️  Function calling validation did not pass. "
                "The agent may not work correctly with this model. "
                f"Details: {result}"
            )

        return result

    async def cleanup(self):
        """Clean up resources (close HTTP connections)."""
        await self.grist_service.close()
        logger.info("GristAgent resources cleaned up")

    async def run(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Run the agent with a user message.

        This method implements a custom agent execution loop using LangChain components:
        1. Builds conversation messages (system prompt + history + user message)
        2. Calls LLM with tools bound
        3. Executes any tool calls made by the LLM
        4. Continues until LLM provides final answer (no more tool calls)

        Args:
            user_message: The user's input message
            chat_history: Optional list of previous messages

        Returns:
            Dictionary with:
                - output: The agent's response
                - intermediate_steps: List of (tool_call, result) tuples
                - success: Whether the execution was successful
                - error: Error message if failed
                - metrics: Execution metrics (iterations, tool calls, failures)
        """
        try:
            # Validate function calling on first run if requested
            if (
                self.validate_function_calling_on_init
                and not self.function_calling_validated
            ):
                validation_result = await self.validate_function_calling()
                if not validation_result.get("test_passed", False):
                    logger.error(
                        "🔴 Function calling validation failed. Agent may not work correctly."
                    )
            # Build messages
            messages = [SystemMessage(content=self.system_prompt)]

            # Add chat history if provided
            if chat_history:
                logger.debug(f"Loading {len(chat_history)} messages from chat history")
                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # Add current user message
            messages.append(HumanMessage(content=user_message))

            # Log user prompt (highly visible)
            logger.info(f"👤 USER: {user_message}")

            # Track intermediate steps
            intermediate_steps = []

            # Agent loop - Track metrics
            tool_call_count = 0
            failed_tool_calls = 0
            iterations_without_tools = 0

            for iteration in range(self.max_iterations):
                logger.debug(
                    f"AGENT ITERATION {iteration + 1}/{self.max_iterations}\n{'='*80}"
                )

                # Call LLM with tools bound
                logger.debug("Calling LLM...")
                response = await self.llm_with_tools.ainvoke(messages)

                # ============================================================
                # CONSOLIDATED RESPONSE LOGGING
                # ============================================================
                # Single consolidated debug log instead of 6 separate ones
                has_content = hasattr(response, "content") and response.content
                has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
                tool_calls_count = len(response.tool_calls) if has_tool_calls else 0

                logger.debug(
                    f"LLM Response: {type(response).__name__}, content={bool(has_content)}, tool_calls={tool_calls_count}"
                )

                # Log content preview only if present
                if has_content:
                    content_preview = (
                        response.content[:200]
                        if len(response.content) > 200
                        else response.content
                    )
                    logger.debug(
                        f"Content preview: {content_preview}{'...' if len(response.content) > 200 else ''}"
                    )

                # Log tool calls details only if present
                if has_tool_calls:
                    for idx, tc in enumerate(response.tool_calls):
                        logger.debug(f"Tool {idx + 1}: {tc.get('name', 'unknown')}")
                elif hasattr(response, "tool_calls"):
                    logger.warning(
                        "⚠️  LLM returned empty tool_calls list. "
                        "This may indicate the model doesn't understand function calling properly."
                    )
                    iterations_without_tools += 1
                else:
                    logger.warning(
                        "⚠️  LLM response has no 'tool_calls' attribute. "
                        "This model may not support function calling."
                    )
                    iterations_without_tools += 1

                # Detect suspicious patterns
                if iterations_without_tools >= 3:
                    logger.error(
                        f"🔴 FUNCTION CALLING FAILURE: No tool calls for {iterations_without_tools} consecutive iterations. "
                        f"This strongly suggests the LLM ({settings.openai_model}) doesn't properly support function calling. "
                        f"Consider using a different model (e.g., gpt-4, gpt-3.5-turbo, claude-3-sonnet, mistral-large-latest)."
                    )

                # Check if LLM wants to call tools
                if hasattr(response, "tool_calls") and response.tool_calls:
                    # Reset counter - LLM is calling tools correctly
                    iterations_without_tools = 0

                    logger.info(
                        f"✓ LLM requested {len(response.tool_calls)} tool call(s) - function calling working correctly"
                    )

                    # Add AI message to conversation
                    messages.append(response)

                    # Execute each tool call (in parallel via asyncio)
                    for idx, tool_call in enumerate(response.tool_calls):
                        try:
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            tool_id = tool_call.get("id", "unknown")
                        except (KeyError, TypeError) as e:
                            logger.error(
                                f"🔴 MALFORMED TOOL CALL: Unable to parse tool call structure. "
                                f"Error: {e}, Tool call object: {tool_call}"
                            )
                            failed_tool_calls += 1
                            continue

                        logger.debug(
                            f"Tool Call {idx + 1}/{len(response.tool_calls)}: {tool_name} with {len(tool_args)} args"
                        )

                        tool_call_count += 1

                        if tool_name in self.tools_by_name:
                            # Check if this operation requires confirmation
                            if self.confirmation_handler.should_confirm(
                                tool_name, tool_args
                            ):
                                logger.info(
                                    f"Tool {tool_name} requires confirmation - creating request"
                                )

                                try:
                                    # Create confirmation request
                                    confirmation = await self.confirmation_handler.create_confirmation_request(
                                        tool_name=tool_name,
                                        tool_args=tool_args,
                                        document_id=self.document_id,
                                    )

                                    logger.info(
                                        f"Confirmation created: {confirmation.confirmation_id}"
                                    )

                                    # Return confirmation request to user
                                    return {
                                        "output": None,
                                        "requires_confirmation": True,
                                        "confirmation_request": confirmation.model_dump(),
                                        "intermediate_steps": intermediate_steps,
                                        "success": True,
                                    }

                                except Exception as e:
                                    error_msg = f"Error creating confirmation: {str(e)}"
                                    logger.error(error_msg, exc_info=True)

                                    # Add error message
                                    messages.append(
                                        ToolMessage(
                                            content=error_msg,
                                            tool_call_id=tool_id,
                                        )
                                    )
                                    intermediate_steps.append((tool_call, error_msg))
                                    continue

                            try:
                                # Execute the tool
                                logger.debug(f"Executing tool: {tool_name}...")
                                tool = self.tools_by_name[tool_name]
                                result = await tool.ainvoke(tool_args)

                                # Log result (consolidated)
                                result_str = str(result)
                                preview = (
                                    result_str[:200]
                                    if len(result_str) > 200
                                    else result_str
                                )
                                logger.debug(
                                    f"Tool result: {preview}{'...' if len(result_str) > 200 else ''}"
                                )

                                # Track step
                                intermediate_steps.append((tool_call, result))

                                # Add tool result to messages
                                messages.append(
                                    ToolMessage(
                                        content=str(result),
                                        tool_call_id=tool_id,
                                    )
                                )
                                logger.info(
                                    f"✅ Tool '{tool_name}' executed successfully"
                                )

                            except Exception as e:
                                failed_tool_calls += 1
                                error_msg = (
                                    f"Error executing tool {tool_name}: {str(e)}"
                                )
                                logger.error(
                                    f"❌ Tool '{tool_name}' failed: {str(e)}",
                                    exc_info=True,
                                )

                                # Add error message
                                messages.append(
                                    ToolMessage(
                                        content=f"Error: {str(e)}",
                                        tool_call_id=tool_id,
                                    )
                                )

                                intermediate_steps.append(
                                    (tool_call, f"Error: {str(e)}")
                                )
                        else:
                            error_msg = f"Tool {tool_name} not found"
                            logger.error(error_msg)
                            messages.append(
                                ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_id,
                                )
                            )

                    # Continue loop to get next LLM response
                    continue

                else:
                    # No tool calls - this is the final answer
                    final_content = (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    )
                    # Log final answer (highly visible)
                    logger.info(f"🤖 ASSISTANT: {final_content}")

                    # Log execution summary (consolidated)
                    success_rate = (
                        (tool_call_count - failed_tool_calls) / tool_call_count * 100
                        if tool_call_count > 0
                        else 0
                    )
                    logger.info(
                        f"✅ Agent completed: {tool_call_count} calls, {failed_tool_calls} failed, {success_rate:.1f}% success"
                    )
                    logger.debug(
                        f"Details: {iteration + 1}/{self.max_iterations} iterations, {len(intermediate_steps)} steps"
                    )

                    return {
                        "output": response.content,
                        "intermediate_steps": intermediate_steps,
                        "success": True,
                        "metrics": {
                            "iterations": iteration + 1,
                            "tool_calls": tool_call_count,
                            "failed_tool_calls": failed_tool_calls,
                        },
                    }

            # Max iterations reached
            logger.error(f"⚠️  Agent reached max iterations ({self.max_iterations})")
            logger.info(
                f"📊 Max iterations: {tool_call_count} calls, {failed_tool_calls} failed, {iterations_without_tools} no-tool iterations"
            )

            # Provide diagnostic information
            if tool_call_count == 0:
                logger.error(
                    "🔴 CRITICAL: Agent made 0 tool calls across all iterations. "
                    "This indicates a serious function calling compatibility issue."
                )
            elif failed_tool_calls / tool_call_count > 0.5:
                logger.error(
                    f"🔴 CRITICAL: High failure rate ({failed_tool_calls}/{tool_call_count}). "
                    "The LLM is calling tools but they're failing frequently."
                )

            return {
                "output": "I apologize, but I've reached the maximum number of steps. Please try rephrasing your request.",
                "intermediate_steps": intermediate_steps,
                "success": False,
                "error": "Max iterations reached",
                "metrics": {
                    "iterations": self.max_iterations,
                    "tool_calls": tool_call_count,
                    "failed_tool_calls": failed_tool_calls,
                    "iterations_without_tools": iterations_without_tools,
                },
            }

        except Exception as e:
            logger.error(f"❌ Agent execution failed: {str(e)}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            return {
                "output": f"I encountered an error: {str(e)}. Please try again or rephrase your request.",
                "intermediate_steps": [],
                "success": False,
                "error": str(e),
                "metrics": {
                    "iterations": 0,
                    "tool_calls": 0,
                    "failed_tool_calls": 0,
                },
            }

    def update_context(
        self,
        page_name: str,
        page_id: int,
        table_id: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> None:
        """
        Update the current page and table context.

        Args:
            page_name: New page name
            page_id: New page ID
            table_id: New table ID (optional)
            table_name: New table name (optional)
        """
        self.current_page_name = page_name
        self.current_page_id = page_id
        if table_id is not None:
            self.current_table_id = table_id
        if table_name is not None:
            self.current_table_name = table_name
        # Regenerate system prompt with new context
        self.system_prompt = get_system_prompt(
            current_page_name=page_name,
            current_page_id=page_id,
            current_table_id=self.current_table_id,
            current_table_name=self.current_table_name,
        )
        logger.info(f"Context updated to page '{page_name}' (id: {page_id})")
