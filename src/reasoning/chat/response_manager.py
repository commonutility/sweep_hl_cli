"""
Response Manager for handling LLM responses and routing them appropriately.
This module takes the initial output from the reasoning model and determines
whether to return text directly or process tool calls.
"""

import json
from typing import Dict, Any, List, Optional
from .tool_handler import ToolHandler


class ResponseManager:
    """Manages responses from the LLM and routes them appropriately."""
    
    def __init__(self):
        """Initialize the ResponseManager with a ToolHandler."""
        self.tool_handler = ToolHandler()
    
    def process_response(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the response from the LLM.
        
        Args:
            llm_response: The response dictionary from the LLM containing:
                - type: "text_response", "tool_call", or "error"
                - Other fields depending on the type
        
        Returns:
            A dictionary containing:
                - type: "text" or "tool_result"
                - content: The text content or tool execution results
                - tool_calls: List of tool calls made (if any)
        """
        response_type = llm_response.get("type")
        
        print(f"[ResponseManager] Processing response of type: {response_type}")
        print(f"[ResponseManager] Full LLM response: {json.dumps(llm_response, indent=2)}")
        
        if response_type == "text_response":
            # Direct text response - no tool calls
            print("[ResponseManager] Processing text-only response")
            return {
                "type": "text",
                "content": llm_response.get("llm_response_text", ""),
                "tool_calls": None
            }
        
        elif response_type == "tool_call":
            # Tool call response - need to execute the tool
            print("[ResponseManager] Processing tool call response")
            
            function_name = llm_response.get("function_name")
            arguments = llm_response.get("arguments", {})
            tool_call_id = llm_response.get("tool_call_id")
            
            # Log the tool call explicitly
            print(f"[ResponseManager] TOOL CALL DETECTED:")
            print(f"  - Function: {function_name}")
            print(f"  - Arguments: {json.dumps(arguments, indent=2)}")
            print(f"  - Tool Call ID: {tool_call_id}")
            
            # Execute the tool through the tool handler
            tool_result = self.tool_handler.execute_tool(function_name, arguments)
            
            # Format the response
            return {
                "type": "tool_result",
                "content": tool_result,
                "tool_calls": [{
                    "function": function_name,
                    "arguments": arguments,
                    "result": tool_result,
                    "tool_call_id": tool_call_id
                }]
            }
        
        elif response_type == "error":
            # Error response
            print(f"[ResponseManager] Processing error response: {llm_response.get('error_message', 'Unknown error')}")
            return {
                "type": "text",
                "content": f"Error: {llm_response.get('error_message', 'An unknown error occurred')}",
                "tool_calls": None,
                "error": True
            }
        
        else:
            # Unknown response type
            print(f"[ResponseManager] Unknown response type: {response_type}")
            return {
                "type": "text",
                "content": "I received an unexpected response format.",
                "tool_calls": None,
                "error": True
            }
    
    def format_for_chat(self, processed_response: Dict[str, Any]) -> str:
        """
        Format the processed response for display in the chat.
        
        Args:
            processed_response: The processed response from process_response()
        
        Returns:
            A formatted string for display in the chat
        """
        if processed_response.get("type") == "text":
            return processed_response.get("content", "")
        
        elif processed_response.get("type") == "tool_result":
            # For now, just return the raw tool result
            # This can be enhanced later with better formatting
            content = processed_response.get("content")
            
            # If it's a string, return it directly
            if isinstance(content, str):
                return content
            
            # If it's a list or dict, convert to JSON for display
            try:
                return json.dumps(content, indent=2)
            except:
                return str(content)
        
        return "No response content available." 