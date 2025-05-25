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

if __name__ == '__main__':
    # Basic test to print the tools
    tools = get_database_query_tools()
    import json
    print(json.dumps(tools, indent=2)) 