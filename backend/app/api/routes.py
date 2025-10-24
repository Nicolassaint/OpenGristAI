"""
API Routes

FastAPI route handlers for the Grist AI Assistant.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Header

from app.models import (
    ChatRequest,
    ChatResponse,
    ConfirmationDecision,
    ConfirmationResponse,
    ConfirmationStatus,
    HealthResponse,
    ToolCall,
    UIMessage,
)
from app.core.agent import GristAgent
from app.core.confirmation import get_confirmation_service
from app.core.tools import get_all_tools, set_grist_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Service status and version.
    """
    return HealthResponse(status="healthy", version="0.1.0")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, x_api_key: str = Header(..., description="Grist access token")
) -> ChatResponse:
    """
    Main chat endpoint for the Grist AI Assistant.

    This endpoint is called by the Grist front-end widget with a conversation
    and expects a response with optional metadata (SQL queries, tool calls, etc.)

    Args:
        request: Chat request with messages and document context
        x_api_key: Grist access token from header

    Returns:
        Assistant's response with metadata

    Raises:
        HTTPException: If the request fails
    """
    logger.info(f"Received chat request for document: {request.documentId}")
    logger.debug(f"Messages count: {len(request.messages)}")
    logger.debug(f"API key present: {'Yes' if x_api_key else 'No'}")

    try:
        # Extract the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")

        last_user_message = user_messages[-1]

        # Extract text from message parts or content
        user_text = ""
        if last_user_message.parts:
            # Extract text from parts
            for part in last_user_message.parts:
                if isinstance(part, dict) and part.get("type") == "text":
                    user_text = part.get("text", "")
                    break
        elif last_user_message.content:
            user_text = last_user_message.content

        if not user_text:
            raise HTTPException(status_code=400, detail="No message text found")

        logger.info(f"User message: {user_text[:100]}...")

        # Initialize the agent with document context
        agent = GristAgent(
            document_id=request.documentId,
            grist_token=x_api_key,
            current_page_name="data",  # TODO: Get from request if needed
            current_page_id=1,
            current_table_id=request.currentTableId,
            current_table_name=request.currentTableName,
        )

        try:
            # Convert messages to chat history format
            chat_history = _convert_ui_messages_to_history(request.messages[:-1])

            # Run the agent
            result = await agent.run(
                user_message=user_text,
                chat_history=chat_history,
            )

            # Check if confirmation is required
            if result.get("requires_confirmation"):
                logger.info("Operation requires user confirmation")

                from app.models import settings

                return ChatResponse(
                    response=None,
                    requires_confirmation=True,
                    confirmation_request=result.get("confirmation_request"),
                    agent_used=settings.openai_model,
                )

            # Extract SQL query from tool calls if present
            sql_query = _extract_sql_query(result.get("intermediate_steps", []))

            # Format tool calls for response
            tool_calls = None
            if result.get("intermediate_steps"):
                tool_calls = _format_tool_calls(result["intermediate_steps"])

            # Build response
            from app.models import settings

            response = ChatResponse(
                response=result["output"],
                sql_query=sql_query,
                agent_used=settings.openai_model,
                tool_calls=tool_calls,
                error=result.get("error") if not result["success"] else None,
            )

            logger.info(
                f"Chat completed: {len(tool_calls) if tool_calls else 0} tool calls"
            )

            return response

        finally:
            # Always cleanup agent resources
            await agent.cleanup()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}", exc_info=True)
        return ChatResponse(
            response=f"I encountered an error: {str(e)}. Please try again.",
            error=str(e),
        )


def _convert_ui_messages_to_history(messages: List[UIMessage]) -> List[Dict[str, str]]:
    """
    Convert UIMessage format to simple chat history format.

    Args:
        messages: List of UIMessage objects

    Returns:
        List of dicts with 'role' and 'content'
    """
    history = []

    for msg in messages:
        content = ""

        # Extract text from parts or content field
        if msg.parts:
            for part in msg.parts:
                if isinstance(part, dict) and part.get("type") == "text":
                    content = part.get("text", "")
                    break
        elif msg.content:
            content = msg.content

        if content:
            history.append({"role": msg.role, "content": content})

    return history


def _extract_sql_query(intermediate_steps: List[tuple]) -> str | None:
    """
    Extract SQL query from tool calls if present.

    Args:
        intermediate_steps: List of (tool_call_dict, result) tuples

    Returns:
        SQL query string or None
    """
    for tool_call, _ in intermediate_steps:
        # tool_call is a dict with 'name' and 'args' keys
        if isinstance(tool_call, dict) and tool_call.get("name") == "query_document":
            query = tool_call.get("args", {}).get("query")
            if query:
                return query

    return None


def _format_tool_calls(intermediate_steps: List[tuple]) -> List[ToolCall]:
    """
    Format intermediate steps into tool calls.

    Args:
        intermediate_steps: List of (tool_call_dict, result) tuples

    Returns:
        List of formatted ToolCall objects
    """
    tool_calls = []

    for tool_call, output in intermediate_steps:
        # tool_call is a dict with 'name', 'args', and 'id' keys
        if isinstance(tool_call, dict):
            tool_calls.append(
                ToolCall(
                    tool_name=tool_call.get("name", "unknown"),
                    tool_input=tool_call.get("args", {}),
                    tool_output=output,
                )
            )

    return tool_calls


@router.post("/chat/confirm", response_model=ConfirmationResponse)
async def confirm_operation(
    decision: ConfirmationDecision,
    x_api_key: str = Header(..., description="Grist access token"),
) -> ConfirmationResponse:
    """
    Confirm or reject a pending destructive operation.

    This endpoint is called after the user reviews a confirmation request
    from the /chat endpoint and decides whether to proceed.

    Args:
        decision: User's decision (approved or rejected)
        x_api_key: Grist access token from header

    Returns:
        ConfirmationResponse with operation result if approved

    Raises:
        HTTPException: If confirmation not found or expired
    """
    logger.info(
        f"Received confirmation decision for {decision.confirmation_id}: "
        f"{'approved' if decision.approved else 'rejected'}"
    )

    confirmation_service = get_confirmation_service()

    if not decision.approved:
        # User rejected the operation
        success = confirmation_service.reject_confirmation(decision.confirmation_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Confirmation {decision.confirmation_id} not found or already processed",
            )

        return ConfirmationResponse(
            confirmation_id=decision.confirmation_id,
            status=ConfirmationStatus.REJECTED,
            message="Operation cancelled by user",
        )

    # User approved - execute the operation
    confirmation_request = confirmation_service.approve_confirmation(
        decision.confirmation_id
    )

    if confirmation_request is None:
        raise HTTPException(
            status_code=404,
            detail=f"Confirmation {decision.confirmation_id} not found or expired",
        )

    # Execute the tool
    from app.services.grist_service import GristService
    from app.models import settings

    # Create Grist service with the access token and correct base URL
    grist_service = GristService(
        document_id=confirmation_request.tool_args.get("document_id", "unknown"),
        access_token=x_api_key,
        base_url=settings.grist_base_url,  # Use the correct base URL
    )

    # Set for tools to use
    set_grist_service(grist_service)

    # Find and execute the tool
    tools = get_all_tools()
    tool = next((t for t in tools if t.name == confirmation_request.tool_name), None)

    if tool is None:
        raise HTTPException(
            status_code=500,
            detail=f"Tool {confirmation_request.tool_name} not found",
        )

    logger.info(f"Executing confirmed operation: {confirmation_request.tool_name}")

    try:
        # Execute the tool
        result = await tool.ainvoke(confirmation_request.tool_args)

        # Cleanup
        await grist_service.close()

        logger.info(
            f"Confirmed operation {confirmation_request.tool_name} executed successfully"
        )

        return ConfirmationResponse(
            confirmation_id=decision.confirmation_id,
            status=ConfirmationStatus.APPROVED,
            message=f"Operation completed successfully: {confirmation_request.preview.description}",
            result=result,
        )

    except Exception as e:
        logger.error(f"Error executing confirmed operation: {str(e)}", exc_info=True)
        # Cleanup even on error
        await grist_service.close()

        return ConfirmationResponse(
            confirmation_id=decision.confirmation_id,
            status=ConfirmationStatus.APPROVED,
            message=f"Operation failed: {str(e)}",
        )
