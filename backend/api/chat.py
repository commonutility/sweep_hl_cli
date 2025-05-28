from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import json

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.reasoning.llm_client import LLMClient
from src.reasoning.chat import ResponseManager
from src.hyperliquid_wrapper.database_handlers.database_manager import DBManager

router = APIRouter()

# Initialize services
llm_client = LLMClient()
response_manager = ResponseManager()
db_manager = DBManager()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    type: str = "text"  # "text", "tool_response", "ui_action", "error"
    ui_actions: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process a chat message and return a response.
    This endpoint integrates with the LLM client and executes any necessary tools.
    """
    try:
        # Get or create session ID
        session_id = message.session_id or db_manager.generate_session_id()
        
        # Add user message to conversation history
        db_manager.add_conversation_message(session_id, "user", message.message)
        
        # Get conversation history
        history = db_manager.get_conversation_history(session_id)
        
        # Convert history to format expected by LLM
        conversation_history = []
        for msg in history:
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get LLM response with conversation history
        llm_response = llm_client.decide_action_with_llm(
            message.message,
            conversation_history=conversation_history[:-1]  # Exclude the current message
        )
        
        # Process the response through the ResponseManager
        processed_response = response_manager.process_response(llm_response)
        
        # Extract the message and other data
        response_message = processed_response.get("message", "")
        response_type = processed_response.get("type", "text")
        ui_actions = processed_response.get("ui_actions")
        tool_results = processed_response.get("tool_results")
        
        # Add logging to trace UI actions
        print(f"[Chat API] Processed response type: {response_type}")
        print(f"[Chat API] UI actions present: {ui_actions is not None}")
        if ui_actions:
            print(f"[Chat API] UI actions: {json.dumps(ui_actions, indent=2)}")
        
        # Add assistant response to conversation history
        db_manager.add_conversation_message(session_id, "assistant", response_message)
        
        # Log the final response being sent
        print(f"[Chat API] Sending response with type: {response_type}")
        print(f"[Chat API] Response has UI actions: {ui_actions is not None and len(ui_actions) > 0}")
        
        # Return the response with all necessary data
        return ChatResponse(
            response=response_message,
            session_id=session_id,
            type=response_type,
            ui_actions=ui_actions,
            tool_results=tool_results
        )
        
    except Exception as e:
        print(f"[Chat API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 