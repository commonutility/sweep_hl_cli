from fastapi import APIRouter, HTTPException
from backend.api.models import ChatRequest, ChatResponse
from typing import Any
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the reasoning components
from src.reasoning.llm_client import LLMClient
from src.reasoning.chat import ResponseManager
from src.reasoning.tools import get_database_query_tools
from src.hyperliquid_wrapper.database_handlers.database_manager import (
    initialize_database, get_current_positions, get_all_trades, get_tracked_open_orders,
    add_conversation_message, get_conversation_history
)

# Create router
router = APIRouter()

# Initialize LLM client and ResponseManager
llm_client = LLMClient()
response_manager = ResponseManager()

# Initialize database on startup
try:
    initialize_database()
    print("[Backend] Database initialized successfully.")
except Exception as e:
    print(f"[Backend] Warning: Could not initialize database: {e}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message through the LLM and return the response.
    This integrates with the existing reasoning_demo logic.
    """
    import uuid
    
    try:
        # Get or generate session ID
        session_id = request.session_id or str(uuid.uuid4())
        user_message = request.message
        
        # Save user message to conversation history
        add_conversation_message(session_id, "user", user_message)
        
        # Get conversation history for context
        history = get_conversation_history(session_id, limit=20)
        
        # Process through LLM with tool support and history
        llm_result = llm_client.decide_action_with_llm(user_message, history)
        
        # Process the LLM response through the ResponseManager
        processed_response = response_manager.process_response(llm_result)
        
        # Format the response for chat display
        response_text = response_manager.format_for_chat(processed_response)
        
        # Extract tool calls if any
        tool_calls_made = processed_response.get("tool_calls", None)
        
        # Save assistant response to conversation history
        if response_text:
            add_conversation_message(
                session_id, 
                "assistant", 
                response_text,
                tool_calls_made if tool_calls_made else None
            )
        
        return ChatResponse(
            response=response_text if response_text else "I couldn't process that request.",
            tool_calls=tool_calls_made if tool_calls_made else None,
            session_id=session_id
        )
        
    except Exception as e:
        print(f"[Backend] Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            response="Sorry, I encountered an error processing your request.",
            error=str(e)
        ) 