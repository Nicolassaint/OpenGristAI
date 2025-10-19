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
        base_url: Optional[str] = None,
        max_iterations: Optional[int] = None,
        verbose: Optional[bool] = None,
        enable_confirmations: bool = True,
    ):
        """
        Initialize the Grist AI Agent.

        Args:
            document_id: Grist document ID or name
            grist_token: JWT access token from Grist widget
            current_page_name: Name of the current page
            current_page_id: ID of the current page
            base_url: Base URL for Grist API (defaults to settings.grist_base_url)
            max_iterations: Maximum number of tool calls allowed (defaults to settings.agent_max_iterations)
            verbose: Whether to log agent actions (defaults to settings.agent_verbose)
            enable_confirmations: Whether to require confirmation for destructive operations (default: True)
        """
        self.document_id = document_id
        self.grist_token = grist_token
        # Use centralized settings with optional overrides
        self.base_url = base_url or settings.grist_base_url
        self.current_page_name = current_page_name
        self.current_page_id = current_page_id
        self.max_iterations = max_iterations or settings.agent_max_iterations
        self.verbose = verbose if verbose is not None else settings.agent_verbose
        self.enable_confirmations = enable_confirmations

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
        from app.core.confirmation_handler import ConfirmationHandler

        self.confirmation_handler = ConfirmationHandler(
            grist_service=self.grist_service,
            enabled=enable_confirmations,
        )

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
        )

        logger.info(
            f"GristAgent initialized for document '{document_id}', "
            f"{len(self.tools)} tools, max_iterations={max_iterations}, "
            f"base_url={self.base_url}"
        )

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

        TODO:
            - Add error recovery for failed tool calls
            - Implement confirmation workflow for destructive operations
            - Add conversation context tracking
        """
        try:
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

            # Log user prompt
            logger.debug("=" * 80)
            logger.debug("USER PROMPT:")
            logger.debug(user_message)
            logger.debug("=" * 80)

            # Track intermediate steps
            intermediate_steps = []

            # Agent loop
            for iteration in range(self.max_iterations):
                logger.debug(f"\n{'='*80}")
                logger.debug(f"AGENT ITERATION {iteration + 1}/{self.max_iterations}")
                logger.debug(f"{'='*80}")

                # Call LLM with tools bound
                logger.debug("Calling LLM...")
                response = await self.llm_with_tools.ainvoke(messages)

                # Log LLM response
                if hasattr(response, "content") and response.content:
                    logger.debug(f"LLM Response Content: {response.content[:500]}...")

                logger.debug(f"LLM wants to call tools: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}")

                # Check if LLM wants to call tools
                if hasattr(response, "tool_calls") and response.tool_calls:
                    logger.debug(f"LLM requested {len(response.tool_calls)} tool call(s)")

                    # Add AI message to conversation
                    messages.append(response)

                    # Execute each tool call (in parallel via asyncio)
                    for idx, tool_call in enumerate(response.tool_calls):
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_id = tool_call.get("id", "unknown")

                        logger.debug(f"\n--- Tool Call {idx + 1}/{len(response.tool_calls)} ---")
                        logger.debug(f"Tool: {tool_name}")
                        logger.debug(f"Args: {tool_args}")
                        logger.debug(f"ID: {tool_id}")

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

                                # Log result
                                result_str = str(result)
                                if len(result_str) > 500:
                                    logger.debug(f"Tool result (truncated): {result_str[:500]}...")
                                else:
                                    logger.debug(f"Tool result: {result_str}")

                                # Track step
                                intermediate_steps.append((tool_call, result))

                                # Add tool result to messages
                                messages.append(
                                    ToolMessage(
                                        content=str(result),
                                        tool_call_id=tool_id,
                                    )
                                )
                                logger.debug(f"✓ Tool {tool_name} executed successfully")

                            except Exception as e:
                                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                                logger.error(error_msg, exc_info=True)

                                # Add error message
                                messages.append(
                                    ToolMessage(
                                        content=f"Error: {str(e)}",
                                        tool_call_id=tool_id,
                                    )
                                )

                                intermediate_steps.append((tool_call, f"Error: {str(e)}"))
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
                    logger.debug(f"\n{'='*80}")
                    logger.debug("FINAL ANSWER:")
                    logger.debug(response.content if hasattr(response, 'content') else response)
                    logger.debug(f"{'='*80}\n")

                    logger.info("Agent execution completed successfully")
                    logger.debug(f"Total intermediate steps: {len(intermediate_steps)}")

                    return {
                        "output": response.content,
                        "intermediate_steps": intermediate_steps,
                        "success": True,
                    }

            # Max iterations reached
            logger.warning(f"Agent reached max iterations ({self.max_iterations})")
            return {
                "output": "I apologize, but I've reached the maximum number of steps. Please try rephrasing your request.",
                "intermediate_steps": intermediate_steps,
                "success": False,
                "error": "Max iterations reached",
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
            return {
                "output": f"I encountered an error: {str(e)}. Please try again or rephrase your request.",
                "intermediate_steps": [],
                "success": False,
                "error": str(e),
            }

    def update_context(self, page_name: str, page_id: int) -> None:
        """
        Update the current page context.

        Args:
            page_name: New page name
            page_id: New page ID
        """
        self.current_page_name = page_name
        self.current_page_id = page_id
        # Regenerate system prompt with new context
        self.system_prompt = get_system_prompt(
            current_page_name=page_name,
            current_page_id=page_id,
        )
        logger.info(f"Context updated to page '{page_name}' (id: {page_id})")


# TODO: Implement conversation memory
# - Use LangChain's ConversationBufferMemory or similar
# - Store conversation history in Redis
# - Implement context window management (summarization for long conversations)

# TODO: Add streaming support
# - Stream agent responses as they're generated
# - Stream tool call results
# - Implement server-sent events (SSE) in FastAPI

# TODO: Implement confirmation workflow
# - Detect destructive operations (delete, update multiple records)
# - Ask user for confirmation before executing
# - Show preview of what will be changed

# TODO: Add agent monitoring
# - Track agent execution time
# - Log all tool calls with inputs/outputs
# - Track success/failure rates
# - Implement alerting for repeated failures
