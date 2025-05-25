import json
from ..database_handlers.database_manager import add_trade, initialize_database, remove_open_order

# Ensure database is initialized when this handler is loaded 
# (though typically main script should handle initialization)
# initialize_database() 
# Commented out: Best practice is for the main application/script to explicitly initialize the DB.

def user_fill_handler(fill_message_data):
    """
    Handles raw WebSocket messages for 'userFills' subscriptions.
    Parses the message and passes individual fills to add_trade.

    Args:
        fill_message_data (dict or list): The 'data' part of a WebSocket message 
                                         expected to contain fill information.
                                         Can be a dict with a 'fills' list, or sometimes
                                         just a list of fills (though API usually wraps in dict).
    """
    print(f"[FillHandler] Received data: {json.dumps(fill_message_data, indent=2, default=str)}")

    fills_to_process = []

    if isinstance(fill_message_data, dict):
        if "fills" in fill_message_data and isinstance(fill_message_data["fills"], list):
            fills_to_process = fill_message_data["fills"]
            if fill_message_data.get("isSnapshot") == True:
                print("[FillHandler] Processing snapshot of user fills.")
            else:
                print("[FillHandler] Processing streaming user fill update.")
        else:
            # Sometimes a single fill might come not wrapped in the 'fills' list, though less common for userFills
            # Check if the dict itself is a fill object by looking for common fill keys
            if all(key in fill_message_data for key in ['coin', 'px', 'sz', 'side', 'time', 'oid', 'tid']):
                fills_to_process.append(fill_message_data)
                print("[FillHandler] Processing single fill object (passed as dict).")
            else:
                print(f"[FillHandler] Received dict, but no 'fills' list or recognized fill structure: {fill_message_data}")
                return

    elif isinstance(fill_message_data, list):
        # If the entire data payload is a list of fills (less common for userFills subscription ack but possible for other contexts)
        fills_to_process = fill_message_data
        print("[FillHandler] Processing list of fills.")
    else:
        print(f"[FillHandler] Received unhandled data type: {type(fill_message_data)}")
        return

    if not fills_to_process:
        print("[FillHandler] No fills found in the received data to process.")
        return

    for fill_data in fills_to_process:
        if not isinstance(fill_data, dict):
            print(f"[FillHandler] Skipping non-dict item in fills list: {fill_data}")
            continue
        try:
            # Ensure necessary fields are present for the database
            required_fields = ['tid', 'oid', 'coin', 'side', 'px', 'sz', 'time']
            if not all(key in fill_data for key in required_fields):
                print(f"[FillHandler] Skipping fill due to missing required fields: {fill_data}")
                continue

            order_id_from_fill = fill_data.get('oid')
            print(f"[FillHandler] Processing fill: Trade ID {fill_data.get('tid')} for Order ID {order_id_from_fill}, Coin {fill_data.get('coin')}")
            
            add_trade(fill_data) # This will call the function from database_manager
            print(f"[FillHandler] Successfully processed and attempted to add trade ID {fill_data.get('tid')} to DB.")

            # After successfully adding the trade, remove it from open_orders_tracking
            if order_id_from_fill:
                remove_open_order(order_id_from_fill)
            else:
                print(f"[FillHandler] Could not determine Order ID from fill to remove from tracking. Fill data: {fill_data}")

        except Exception as e:
            print(f"[FillHandler] Error processing fill data or adding to DB: {e}")
            print(f"  Problematic fill_data: {fill_data}")
            # Optionally, re-raise or handle more gracefully
            # raise

def handle_cancel_order_response(cancel_result: dict, order_id: int):
    """
    Parses and prints the status of a cancel order API call.

    Args:
        cancel_result (dict): The raw response from the cancel order API call.
        order_id (int): The ID of the order that was attempted to be cancelled.
    """
    print(f"[FillHandler] Parsing cancel order response for Order ID {order_id}: {json.dumps(cancel_result, indent=2)}")

    if not cancel_result or not isinstance(cancel_result, dict):
        print(f"[FillHandler] Cancellation response for order {order_id} is empty or not a dictionary.")
        return

    status = cancel_result.get("status")

    if status == "ok":
        response_data = cancel_result.get("response", {}).get("data", {})
        statuses_array = response_data.get("statuses", []) # Note: Hyperliquid SDK might return this as just 'statuses'
        
        if not statuses_array and isinstance(response_data, list): # Fallback if 'data' itself is the statuses list
            statuses_array = response_data
        elif not statuses_array and isinstance(response_data.get("statuses"), list): # another common pattern
            statuses_array = response_data.get("statuses")

        if statuses_array and isinstance(statuses_array, list) and len(statuses_array) > 0:
            first_status_detail = statuses_array[0]
            if isinstance(first_status_detail, dict):
                if "canceled" in first_status_detail: # Ideal scenario for an open order
                    print(f"[FillHandler] Order {order_id} successfully cancelled. Details: {first_status_detail['canceled']}")
                elif "error" in first_status_detail:
                    error_msg = first_status_detail['error']
                    print(f"[FillHandler] API info for order {order_id} cancellation: {error_msg}")
                    if "already canceled, or filled" in error_msg or "Order was never placed" in error_msg:
                        print(f"          (This is expected if the order was already processed/filled or never active.)")
                else:
                    print(f"[FillHandler] Cancellation status for order {order_id} has details: {first_status_detail}")
            else:
                 print(f"[FillHandler] Cancellation detail format unexpected for order {order_id}: {first_status_detail}")
        else:
            # This case handles if the cancel was accepted but no specific status in statuses array (e.g. already processed)
            print(f"[FillHandler] Order {order_id} cancellation processed by API (status ok), no further specific status details in expected array.")
            print(f"          This often means the order was already filled or previously cancelled.")

    elif status == "err":
        error_response = cancel_result.get('response', "No error details provided.")
        print(f"[FillHandler] API reported an error trying to cancel order {order_id}: {error_response}")
    else:
        print(f"[FillHandler] Cancellation response format unexpected for order {order_id} (unknown top-level status).")

if __name__ == '__main__':
    # Example usage for fill_handler (requires database_manager.py to be correct)
    print("Running fill_handler.py example...")
    print("Initializing database via fill_handler's direct call (for testing only)...")
    # For this test, explicitly initialize the DB if it hasn't been for some reason
    # In a real app, demo_with_credentials.py would call initialize_database() once at the start.
    try:
        initialize_database()
    except Exception as e:
        print(f"DB init error in fill_handler test: {e}")

    print("\nSimulating receiving WebSocket fill messages...")
    #dadfsfsd
    # Example 1: Snapshot message
    snapshot_message = {
        "channel": "userFills",
        "isSnapshot": True,
        "user": "0xYourAddress",
        "data": {
            "fills": [
                {"tid": 1001, "oid": 2001, "coin": "BTC", "side": "B", "px": "55000", "sz": "0.01", "time": 1678886400000, "fee": "0.5", "closedPnl": "0", "hash": "0xaaa", "crossed": True, "startPosition": "0", "dir": "Open Long", "feeToken": "USDC"},
                {"tid": 1002, "oid": 2002, "coin": "ETH", "side": "A", "px": "4000", "sz": "0.1", "time": 1678886500000, "fee": "0.4", "closedPnl": "0", "hash": "0xbbb", "crossed": False, "startPosition": "0", "dir": "Open Short", "feeToken": "USDC"}
            ]
        }
    }
    print("\n--- Handling Snapshot Message ---")
    if snapshot_message['channel'] == 'userFills':
         user_fill_handler(snapshot_message['data'])
    #
    # Example 2: Streaming update (single fill)
    stream_update_message = {
        "channel": "userFills",
        "user": "0xYourAddress",
        "data": {
            "fills": [
                {"tid": 1003, "oid": 2003, "coin": "BTC", "side": "A", "px": "55500", "sz": "0.005", "time": 1678886600000, "fee": "0.25", "closedPnl": "2.5", "hash": "0xccc", "crossed": True, "startPosition": "0.01", "dir": "Close Long", "feeToken": "USDC"}
            ]
        }
    }
    print("\n--- Handling Stream Update Message ---")
    if stream_update_message['channel'] == 'userFills':
        user_fill_handler(stream_update_message['data'])
    
    # Example 3: Direct fill object (less common for userFills, but testing robustness)
    direct_fill_data = {"tid": 1004, "oid": 2004, "coin": "SOL", "side": "B", "px": "150", "sz": "1", "time": 1678886700000, "fee": "0.15", "closedPnl": "0", "hash": "0xddd", "crossed": True, "startPosition": "0", "dir": "Open Long", "feeToken": "USDC"}
    print("\n--- Handling Direct Fill Data (as dict) ---")
    user_fill_handler(direct_fill_data) # Pass the dict directly

    # Example 4: List of direct fill objects
    list_of_fills = [
        {"tid": 1005, "oid": 2005, "coin": "AVAX", "side": "A", "px": "50", "sz": "10", "time": 1678886800000, "fee": "0.5", "closedPnl": "0", "hash": "0xeee", "crossed": True, "startPosition": "0", "dir": "Open Short", "feeToken": "USDC"},
        {"tid": 1006, "oid": 2006, "coin": "AVAX", "side": "B", "px": "48", "sz": "5", "time": 1678886900000, "fee": "0.24", "closedPnl": "10", "hash": "0xfff", "crossed": True, "startPosition": "-10", "dir": "Close Short", "feeToken": "USDC"}
    ]
    print("\n--- Handling List of Fill Data ---")
    user_fill_handler(list_of_fills) # Pass the list directly

    print("\nfill_handler.py example finished.") 