"""
Tool Handler for executing tool calls from the LLM.
This module handles the execution of specific tools based on the function name
and arguments provided by the LLM.
"""

import json
import sys
import os
from typing import Dict, Any, Optional

# Add parent directories to path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.hyperliquid_wrapper.database_handlers.database_manager import (
    get_all_trades, get_current_positions
)


class ToolHandler:
    """Handles the execution of tool calls from the LLM."""
    
    def __init__(self):
        """Initialize the ToolHandler with necessary dependencies."""
        # Map function names to their handlers
        self.tool_map = {
            "get_all_trades_from_db": self._handle_get_trades,
            "get_current_positions_from_db": self._handle_get_positions
        }
    
    def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool based on the function name and arguments.
        
        Args:
            function_name: The name of the function to execute
            arguments: The arguments to pass to the function
        
        Returns:
            The result of the tool execution
        """
        print(f"[ToolHandler] Executing tool: {function_name}")
        print(f"[ToolHandler] Arguments: {json.dumps(arguments, indent=2)}")
        
        # Check if the tool exists
        if function_name not in self.tool_map:
            error_msg = f"Unknown tool: {function_name}"
            print(f"[ToolHandler] ERROR: {error_msg}")
            return {"error": error_msg}
        
        try:
            # Execute the tool
            handler = self.tool_map[function_name]
            result = handler(arguments)
            
            print(f"[ToolHandler] Tool execution successful")
            print(f"[ToolHandler] Result type: {type(result)}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing tool {function_name}: {str(e)}"
            print(f"[ToolHandler] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}
    
    def _handle_get_trades(self, arguments: Dict[str, Any]) -> Any:
        """
        Handle the get_all_trades_from_db tool call.
        
        Args:
            arguments: Dictionary containing optional filters (currently unused)
        
        Returns:
            List of trades or error message
        """
        print("[ToolHandler] Handling get_all_trades_from_db")
        
        # Get all trades from database
        trades = get_all_trades()
        
        if trades is None:
            return {"error": "Failed to retrieve trades from database"}
        
        # Convert DataFrame to list of dictionaries for JSON serialization
        if hasattr(trades, 'to_dict'):
            trades_list = trades.to_dict('records')
            print(f"[ToolHandler] Retrieved {len(trades_list)} trades")
            return trades_list
        
        return trades
    
    def _handle_get_positions(self, arguments: Dict[str, Any]) -> Any:
        """
        Handle the get_current_positions_from_db tool call.
        
        Args:
            arguments: Dictionary (currently unused for this function)
        
        Returns:
            Current positions or error message
        """
        print("[ToolHandler] Handling get_current_positions_from_db")
        
        # Get current positions from database
        positions = get_current_positions()
        
        if positions is None:
            return {"error": "Failed to retrieve positions from database"}
        
        # Convert DataFrame to list of dictionaries for JSON serialization
        if hasattr(positions, 'to_dict'):
            positions_list = positions.to_dict('records')
            print(f"[ToolHandler] Retrieved {len(positions_list)} positions")
            return positions_list
        
        return positions 