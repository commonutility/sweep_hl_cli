# src/reasoning/tools.py

def get_database_query_tools():
    """Returns a list of tool definitions for database query functions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_all_trades_from_db",
                "description": "Retrieves all recorded trade history from the local database, ordered by most recent first. Use this to see past trades.",
                "parameters": {
                    "type": "object",
                    "properties": {}, # No parameters for this function
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_positions_from_db",
                "description": "Retrieves current aggregated asset positions (e.g., coin, net size, average entry price) from the local database. Use this to see what you are currently holding.",
                "parameters": {
                    "type": "object",
                    "properties": {}, # No parameters for this function
                    "required": []
                }
            }
        }
        # Future tools for trading actions (market_buy, market_sell, etc.) will be added here.
        # For example:
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "market_buy_order",
        #         "description": "Places a market buy order for a specified symbol and asset size.",
        #         "parameters": {
        #             "type": "object",
        #             "properties": {
        #                 "symbol": {"type": "string", "description": "The trading symbol, e.g., 'BTC', 'ETH'."},
        #                 "asset_size": {"type": "number", "description": "The amount of the asset to buy."}
        #             },
        #             "required": ["symbol", "asset_size"]
        #         }
        #     }
        # }
    ]


def get_ui_rendering_tools():
    """Returns a list of tool definitions for UI rendering functions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "render_asset_view",
                "description": "Display the asset price chart and information for a specific cryptocurrency or asset. Use this when the user asks about prices, charts, or wants to see asset information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The asset symbol to display (e.g., 'BTC', 'ETH', 'SOL')"
                        },
                        "time_range": {
                            "type": "string",
                            "description": "Time range for the chart. Options: '1D', '1W', '1M', '3M', '6M', '1Y'. Default is '6M'",
                            "enum": ["1D", "1W", "1M", "3M", "6M", "1Y"]
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "render_portfolio_view",
                "description": "Display the user's portfolio overview showing all positions, total value, and P&L. Use this when the user asks about their portfolio or overall holdings.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "render_trade_form",
                "description": "Display a trading form for placing buy or sell orders. Use this when the user wants to trade or place an order.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The asset symbol to trade (e.g., 'BTC', 'ETH')"
                        },
                        "side": {
                            "type": "string",
                            "description": "The trade side: 'buy' or 'sell'",
                            "enum": ["buy", "sell"]
                        },
                        "suggested_amount": {
                            "type": "number",
                            "description": "Optional suggested amount to pre-fill in the form"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "render_order_history",
                "description": "Display the user's order history and trade history. Use this when the user asks about past trades or order history.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Optional filter: 'all', 'filled', 'cancelled', 'open'",
                            "enum": ["all", "filled", "cancelled", "open"]
                        }
                    },
                    "required": []
                }
            }
        }
    ]


def get_all_tools():
    """Returns all available tools combining database and UI tools."""
    return get_database_query_tools() + get_ui_rendering_tools()


if __name__ == '__main__':
    # Basic test to print the tools
    tools = get_all_tools()
    import json
    print(json.dumps(tools, indent=2)) 