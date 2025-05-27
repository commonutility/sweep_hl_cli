from fastapi import APIRouter, HTTPException
from backend.api.models import ChatRequest, ChatResponse
from typing import Any
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the reasoning components
from src.reasoning.llm_client import LLMClient
from src.reasoning.tools import get_database_query_tools
from src.hyperliquid_wrapper.database_handlers.database_manager import (
    initialize_database, get_current_positions, get_all_trades, get_tracked_open_orders,
    add_conversation_message, get_conversation_history
)

# Create router
router = APIRouter()

# Initialize LLM client (you'll need to set OPENAI_API_KEY environment variable)
llm_client = LLMClient()

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
        result = llm_client.decide_action_with_llm(user_message, history)
        
        # Extract response and tool calls
        response_text = ""
        tool_calls_made = []
        
        if result and result.get("type") == "text_response":
            # Direct text response from LLM
            response_text = result.get("llm_response_text", "")
            
        elif result and result.get("type") == "tool_call":
            # LLM decided to call a tool
            tool_name = result.get("function_name")
            tool_args = result.get("arguments", {})
            
            # Execute the tool call
            tool_result = execute_tool(tool_name, tool_args)
            
            tool_calls_made.append({
                "tool": tool_name,
                "arguments": tool_args,
                "result": tool_result
            })
            
            # Format the response with tool results
            response_text = f"I'll check that for you.\n\n{format_tool_result(tool_name, tool_result)}"
            
        elif result and result.get("type") == "error":
            # Handle error from LLM
            error_status = result.get("status", "unknown_error")
            error_message = result.get("error_message", "An error occurred")
            response_text = f"I encountered an issue: {error_message}"
        
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
        return ChatResponse(
            response="Sorry, I encountered an error processing your request.",
            error=str(e)
        )

def execute_tool(tool_name: str, tool_args: dict) -> Any:
    """Execute a tool call and return the result."""
    try:
        # Arguments are already parsed as a dictionary from the LLM response
        args = tool_args
            
        # Execute based on tool name
        if tool_name == "get_all_trades":
            return get_all_trades()
        elif tool_name == "get_current_positions":
            return get_current_positions()
        elif tool_name == "get_tracked_open_orders":
            return get_tracked_open_orders()
        else:
            return f"Unknown tool: {tool_name}"
            
    except Exception as e:
        return f"Error executing tool {tool_name}: {str(e)}"

def format_tool_result(tool_name: str, result: Any) -> str:
    """Format tool results for display."""
    if tool_name == "get_all_trades":
        if result and len(result) > 0:
            output = "📊 Recent Trades:\n"
            for trade in result[:5]:  # Show last 5 trades
                output += f"  • {trade.get('coin', 'N/A')}: {trade.get('side', 'N/A')} {trade.get('sz', 'N/A')} @ ${trade.get('px', 'N/A')}\n"
            return output
        else:
            return "📊 No trades found in the database."
            
    elif tool_name == "get_current_positions":
        if result and len(result) > 0:
            output = "💼 Current Positions:\n"
            for position in result:
                output += f"  • {position.get('coin', 'N/A')}: {position.get('net_size', 'N/A')} (Avg: ${position.get('avg_entry_price', 'N/A')})\n"
            return output
        else:
            return "💼 No open positions found."
            
    elif tool_name == "get_tracked_open_orders":
        if result and len(result) > 0:
            output = "📋 Open Orders:\n"
            for order in result:
                output += f"  • {order.get('coin', 'N/A')}: {order.get('side', 'N/A')} {order.get('sz', 'N/A')} @ ${order.get('limit_px', 'N/A')}\n"
            return output
        else:
            return "📋 No open orders found."
            
    return str(result) 