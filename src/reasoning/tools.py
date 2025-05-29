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
                "description": "Display the asset price chart and information for a specific cryptocurrency or trading pair. Use this when the user asks about prices, charts, or wants to see asset information. Supports both single assets (e.g., 'BTC' which defaults to BTC/USD) and trading pairs (e.g., 'ETH' with quote_asset 'SOL' for ETH/SOL).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The base asset symbol to display (e.g., 'BTC', 'ETH', 'SOL')"
                        },
                        "quote_asset": {
                            "type": "string",
                            "description": "The quote asset for the trading pair (e.g., 'USD', 'USDC', 'SOL', 'BTC'). Defaults to 'USD' if not specified.",
                            "default": "USD"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval for the chart. Options: '5m', '1h', '1d'. Default is '1h'",
                            "enum": ["5m", "1h", "1d"],
                            "default": "1h"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "render_multipanel_asset",
                "description": "Display multiple cryptocurrency price charts in a 2x2 grid layout. Use this when the user wants to compare multiple assets or see several charts at once. Perfect for viewing 4 different assets simultaneously.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbols": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Array of asset symbols to display (e.g., ['BTC', 'ETH', 'SOL', 'ARB']). Will display up to 4 assets in a 2x2 grid.",
                            "default": ["BTC", "ETH", "SOL", "ARB"]
                        },
                        "quote_asset": {
                            "type": "string",
                            "description": "The quote asset for all trading pairs (e.g., 'USD', 'USDC'). Defaults to 'USD'.",
                            "default": "USD"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval for all charts. Options: '5m', '1h', '1d'. Default is '1h'",
                            "enum": ["5m", "1h", "1d"],
                            "default": "1h"
                        }
                    },
                    "required": []
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