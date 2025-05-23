import json

def simple_trade_data_handler(trade_payload):
    """
    A simple handler for processing and printing trade data from the stream.

    Args:
        trade_payload (dict): A dictionary containing the trade data.
                              Expected to have keys like 'side', 'price', 'size', 
                              'timestamp', and 'raw' (for the original message).
                              It can also handle a simple {'error': ..., 'raw': ...} dict.
    """
    if not isinstance(trade_payload, dict):
        print(f"[Handler] Received non-dict payload: {type(trade_payload)} - {trade_payload}")
        return

    if "error" in trade_payload:
        print(f"[Handler] Error in payload: {trade_payload['error']}")
        print(f"  Raw data with error: {trade_payload.get('raw')}")
        return

    # Default values for printing
    side = trade_payload.get('side', 'N/A')
    price_str = trade_payload.get('price', 'N/A')
    size_str = trade_payload.get('size', 'N/A')
    timestamp = trade_payload.get('timestamp', 'N/A')
    
    # Attempt to format price and size if they are numbers
    try:
        price = float(price_str)
        price_display = f"${price:,.2f}"
    except (ValueError, TypeError):
        price_display = price_str
        
    try:
        size = float(size_str)
        size_display = f"{size:,.4f}" # Adjust precision as needed
    except (ValueError, TypeError):
        size_display = size_str

    print(f"[Handler] Trade: {side} {size_display} @ {price_display} (Time: {timestamp})")

    # Optionally print raw data if needed for debugging, can be commented out
    # if 'raw' in trade_payload:
    #     print(f"  Raw trade object: {json.dumps(trade_payload['raw'], indent=2)}")

def detailed_trade_data_handler(parsed_trade_data):
    """
    Handles parsed trade data from the Hyperliquid WebSocket stream
    with more detailed parsing based on the structure from hyperliquid_client.py.
    """
    try:
        if isinstance(parsed_trade_data, dict):
            if "channel" in parsed_trade_data and "data" in parsed_trade_data:
                # Standard WebSocket format
                for trade in parsed_trade_data["data"]:
                    if isinstance(trade, dict):
                        side = "🟢 BUY " if trade.get("side") == "B" else "🔴 SELL"
                        price = trade.get("px", "N/A")
                        size = trade.get("sz", "N/A")
                        timestamp = trade.get("time", "N/A")
                        print(f"[Handler] Trade: {side} {size} @ ${price} (Time: {timestamp})")
            elif "data" in parsed_trade_data: # Alternative format (list of trades in 'data')
                data_content = parsed_trade_data["data"]
                if isinstance(data_content, list):
                    for trade in data_content:
                        if isinstance(trade, dict):
                            side = "🟢 BUY " if trade.get("side") == "B" else "🔴 SELL"
                            price = trade.get("px", "N/A")
                            size = trade.get("sz", "N/A")
                            print(f"[Handler] Trade (from list): {side} {size} @ ${price}")
            elif "px" in parsed_trade_data and "sz" in parsed_trade_data: # Direct trade object
                side = "🟢 BUY " if parsed_trade_data.get("side") == "B" else "🔴 SELL"
                price = parsed_trade_data.get("px", "N/A")
                size = parsed_trade_data.get("sz", "N/A")
                print(f"[Handler] Trade (direct): {side} {size} @ ${price}")
            else:
                # A dictionary but not a recognized trade structure
                print(f"[Handler] Received Dict: {json.dumps(parsed_trade_data, indent=2, default=str)}")

        elif isinstance(parsed_trade_data, list): # If the entire message is a list of trades
            for trade_item in parsed_trade_data:
                if isinstance(trade_item, dict) and "px" in trade_item and "sz" in trade_item:
                    side = "🟢 BUY " if trade_item.get("side") == "B" else "🔴 SELL"
                    price = trade_item.get("px", "N/A")
                    size = trade_item.get("sz", "N/A")
                    print(f"[Handler] Trade (from list item): {side} {size} @ ${price}")
                else:
                    print(f"[Handler] Received List Item: {trade_item}")
        else:
            print(f"[Handler] Received Unhandled Data Type: {type(parsed_trade_data)} - {parsed_trade_data}")

    except Exception as e:
        print(f"[Handler] Error processing trade data: {e}")
        print(f"  Raw data causing handler error: {parsed_trade_data}") 