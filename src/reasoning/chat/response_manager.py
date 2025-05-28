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
                - type: 'text_response', 'tool_call', or 'error'
                - Other fields depending on type
                
        Returns:
            Processed response dictionary with:
                - type: 'text', 'tool_response', or 'error'
                - message: The text message (if any)
                - tool_results: Results from tool execution (if any)
                - ui_actions: UI actions to perform (if any)
        """
        response_type = llm_response.get("type")
        
        print(f"[ResponseManager] Processing response of type: {response_type}")
        
        if response_type == "text_response":
            # Direct text response from LLM
            return {
                "type": "text",
                "message": llm_response.get("llm_response_text", ""),
                "status": "success"
            }
            
        elif response_type == "tool_call":
            # LLM wants to call a tool
            function_name = llm_response.get("function_name")
            arguments = llm_response.get("arguments", {})
            tool_call_id = llm_response.get("tool_call_id")
            
            print(f"[ResponseManager] Processing tool call: {function_name}")
            print(f"[ResponseManager] Tool call arguments: {json.dumps(arguments, indent=2)}")
            
            # Create tool call structure
            tool_call = {
                "function": {
                    "name": function_name,
                    "arguments": json.dumps(arguments)
                },
                "id": tool_call_id
            }
            
            # Check if it's a UI tool
            if self.tool_handler.is_ui_tool(function_name):
                print(f"[ResponseManager] Identified as UI tool: {function_name}")
                ui_action = self.tool_handler.handle_ui_tool(tool_call)
                
                # Generate a message to accompany the UI action
                message = self._generate_ui_action_message(function_name, arguments)
                
                return {
                    "type": "ui_action",
                    "message": message,
                    "ui_actions": [ui_action],
                    "status": "success"
                }
            else:
                # It's a data tool
                print(f"[ResponseManager] Identified as data tool: {function_name}")
                result = self.tool_handler.execute_tool(tool_call)
                
                # Format the result for display
                formatted_result = self._format_tool_result(function_name, result)
                
                return {
                    "type": "tool_response",
                    "message": formatted_result["message"],
                    "tool_results": [result],
                    "status": "success"
                }
                
        elif response_type == "error":
            # Error from LLM
            return {
                "type": "error",
                "message": f"Error: {llm_response.get('error_message', 'Unknown error')}",
                "status": llm_response.get("status", "error")
            }
            
        else:
            # Unknown response type
            return {
                "type": "error",
                "message": f"Unknown response type: {response_type}",
                "status": "error_unknown_response_type"
            }
    
    def _generate_ui_action_message(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Generate a user-friendly message for UI actions."""
        messages = {
            "render_asset_view": lambda args: f"Displaying {args.get('symbol', 'asset')}/{args.get('quote_asset', 'USD')} chart...",
            "render_portfolio_view": lambda args: "Displaying your portfolio...",
            "render_trade_form": lambda args: f"Opening {args.get('side', 'trade')} form for {args.get('symbol', 'asset')}...",
            "render_order_history": lambda args: f"Displaying {args.get('filter', 'all')} orders..."
        }
        
        if function_name in messages:
            return messages[function_name](arguments)
        else:
            return f"Executing {function_name}..."
    
    def _format_tool_result(self, function_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format tool execution results for display.
        
        Args:
            function_name: The name of the tool that was executed
            result: The result from tool execution
            
        Returns:
            Formatted result with a message
        """
        if not result.get("success", False):
            return {
                "message": f"Error executing {function_name}: {result.get('error', 'Unknown error')}",
                "data": None
            }
        
        # Format based on function name
        if function_name == "get_all_trades_from_db":
            trades = result.get("result", [])
            if isinstance(trades, list) and len(trades) > 0:
                message = f"Found {len(trades)} trades in the database."
            else:
                message = "No trades found in the database."
                
        elif function_name == "get_current_positions_from_db":
            positions = result.get("result", [])
            if isinstance(positions, list) and len(positions) > 0:
                message = f"You have {len(positions)} open positions."
            else:
                message = "No open positions found."
                
        else:
            message = f"Tool {function_name} executed successfully."
        
        return {
            "message": message,
            "data": result.get("result")
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
            return processed_response.get("message", "")
        
        elif processed_response.get("type") == "tool_response":
            # For now, just return the raw tool result
            # This can be enhanced later with better formatting
            content = processed_response.get("tool_results", [])
            
            # If it's a string, return it directly
            if isinstance(content, str):
                return content
            
            # If it's a list or dict, convert to JSON for display
            try:
                return json.dumps(content, indent=2)
            except:
                return str(content)
        
        return "No response content available." 