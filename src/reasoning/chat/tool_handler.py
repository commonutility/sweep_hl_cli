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
from src.config import config


class ToolHandler:
    """Handles the execution of tool calls from the LLM."""
    
    def __init__(self):
        """Initialize the ToolHandler with necessary dependencies."""
        # Map function names to their handlers
        self.tool_map = {
            "get_all_trades_from_db": self._handle_get_all_trades,
            "get_current_positions_from_db": self._handle_get_current_positions,
        }
        
        # UI tool mapping
        self.ui_tool_map = {
            "render_asset_view": self._handle_render_asset_view,
            "render_portfolio_view": self._handle_render_portfolio_view,
            "render_trade_form": self._handle_render_trade_form,
            "render_order_history": self._handle_render_order_history,
        }
    
    def is_ui_tool(self, function_name: str) -> bool:
        """Check if a function is a UI tool."""
        return function_name in self.ui_tool_map
    
    def execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call and return the result.
        
        Args:
            tool_call: Dictionary containing function name and arguments
            
        Returns:
            Dictionary containing the tool execution result
        """
        function_name = tool_call.get("function", {}).get("name")
        arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
        
        print(f"[ToolHandler] Executing tool: {function_name} with args: {arguments}")
        
        if function_name in self.tool_map:
            try:
                result = self.tool_map[function_name](arguments)
                return {
                    "success": True,
                    "function_name": function_name,
                    "result": result
                }
            except Exception as e:
                print(f"[ToolHandler] Error executing {function_name}: {str(e)}")
                return {
                    "success": False,
                    "function_name": function_name,
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "function_name": function_name,
                "error": f"Unknown tool function: {function_name}"
            }
    
    def handle_ui_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle UI rendering tool calls"""
        function_name = tool_call.get("function", {}).get("name")
        arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
        
        print(f"[ToolHandler] Handling UI tool: {function_name} with args: {arguments}")
        
        if function_name in self.ui_tool_map:
            return self.ui_tool_map[function_name](arguments)
        else:
            return {"error": f"Unknown UI tool: {function_name}"}
    
    # Data tool handlers
    def _handle_get_all_trades(self, args: Dict[str, Any]) -> Any:
        """Handle get_all_trades_from_db tool call."""
        # Network will be determined by the current context
        trades = get_all_trades()
        return trades
    
    def _handle_get_current_positions(self, args: Dict[str, Any]) -> Any:
        """Handle get_current_positions_from_db tool call."""
        # Network will be determined by the current context
        positions = get_current_positions()
        return positions
    
    # UI tool handlers
    def _handle_render_asset_view(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI action for rendering asset view"""
        symbol = args.get("symbol", "BTC").upper()
        quote_asset = args.get("quote_asset", "USD").upper()
        time_range = args.get("time_range", "6M")
        
        print(f"[ToolHandler] Generating render action for asset: {symbol}/{quote_asset}, range: {time_range}")
        
        return {
            "action": "render_component",
            "component": "AssetPage",
            "props": {
                "symbol": symbol,
                "quoteAsset": quote_asset,
                "timeRange": time_range
            },
            "target": "main_panel"
        }
    
    def _handle_render_portfolio_view(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI action for rendering portfolio view"""
        print("[ToolHandler] Generating render action for portfolio view")
        
        return {
            "action": "render_component",
            "component": "PortfolioView",
            "props": {},
            "target": "main_panel"
        }
    
    def _handle_render_trade_form(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI action for rendering trade form"""
        symbol = args.get("symbol", "BTC").upper()
        side = args.get("side", "buy")
        suggested_amount = args.get("suggested_amount")
        
        print(f"[ToolHandler] Generating render action for trade form: {symbol} {side}")
        
        props = {
            "symbol": symbol,
            "side": side
        }
        
        if suggested_amount is not None:
            props["suggestedAmount"] = suggested_amount
        
        return {
            "action": "render_component",
            "component": "TradeForm",
            "props": props,
            "target": "main_panel"
        }
    
    def _handle_render_order_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI action for rendering order history"""
        filter_type = args.get("filter", "all")
        
        print(f"[ToolHandler] Generating render action for order history with filter: {filter_type}")
        
        return {
            "action": "render_component",
            "component": "OrderHistory",
            "props": {
                "filter": filter_type
            },
            "target": "main_panel"
        } 