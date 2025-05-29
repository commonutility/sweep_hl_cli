import sqlite3
import os
from datetime import datetime

# Import network context
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.network_context import get_current_network

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'database')
DATABASE_NAME = os.path.join(DATABASE_DIR, 'trading_data.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def initialize_database():
    """
    Initializes the database by creating necessary tables if they don't exist.
    - trades: Stores individual fill information.
    - positions: Stores current aggregated positions for each coin.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create trades table with network column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,                      -- Hyperliquid's unique trade ID (tid)
        order_id INTEGER,                      -- Hyperliquid's order ID (oid)
        coin TEXT NOT NULL,
        side TEXT NOT NULL,                    -- 'B' (Buy) or 'A' (Sell)
        price REAL NOT NULL,
        size REAL NOT NULL,
        fee REAL,
        timestamp INTEGER NOT NULL,            -- Unix timestamp in milliseconds
        closed_pnl REAL,
        hash TEXT,
        crossed BOOLEAN,
        start_position TEXT,
        dir TEXT,                              -- 'Open Long', 'Close Long', 'Open Short', 'Close Short'
        fee_token TEXT,
        builder_fee REAL,
        network TEXT NOT NULL DEFAULT 'testnet', -- Network: 'mainnet' or 'testnet'
        received_at TEXT DEFAULT CURRENT_TIMESTAMP, -- When the fill was processed by our system
        UNIQUE(trade_id, network)              -- Unique constraint per network
    )
    ''')
    print("[DBManager] 'trades' table initialized or already exists.")

    # Create positions table with network column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        coin TEXT NOT NULL,
        network TEXT NOT NULL DEFAULT 'testnet', -- Network: 'mainnet' or 'testnet'
        net_size REAL NOT NULL DEFAULT 0,
        average_entry_price REAL NOT NULL DEFAULT 0, -- Weighted average entry price
        total_cost REAL NOT NULL DEFAULT 0,          -- Total cost basis for the current position
        unrealized_pnl REAL DEFAULT 0,               -- Will require external price updates to calculate accurately
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (coin, network)                  -- Composite primary key
    )
    ''')
    print("[DBManager] 'positions' table initialized or already exists.")

    # Create open_orders_tracking table with network column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS open_orders_tracking (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,             -- Hyperliquid's order ID (oid)
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,                    -- 'B' (Buy) or 'A' (Sell)
        order_type TEXT NOT NULL,              -- 'market', 'limit', etc.
        price REAL,                            -- For limit orders, null for market
        size REAL NOT NULL,
        network TEXT NOT NULL DEFAULT 'testnet', -- Network: 'mainnet' or 'testnet'
        timestamp_placed INTEGER NOT NULL,      -- Local Unix timestamp (milliseconds) when logged
        UNIQUE(order_id, network)              -- Unique constraint per network
    )
    ''')
    print("[DBManager] 'open_orders_tracking' table initialized or already exists.")

    # Create conversations table for chat history (no network needed for conversations)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,                    -- 'user', 'assistant', 'system'
        content TEXT NOT NULL,
        tool_calls TEXT,                       -- JSON string of tool calls if any
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("[DBManager] 'conversations' table initialized or already exists.")
    
    # Create index for efficient session queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_session_timestamp 
    ON conversations(session_id, timestamp)
    ''')
    
    # Create indexes for network-based queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_trades_network_timestamp 
    ON trades(network, timestamp)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_positions_network 
    ON positions(network)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_orders_network 
    ON open_orders_tracking(network)
    ''')

    conn.commit()
    conn.close()
    print("[DBManager] Database initialization complete.")

def add_trade(trade_data: dict, network: str = None):
    """
    Adds a trade fill to the trades table and updates the positions table.
    'trade_data' is expected to be a dictionary matching Hyperliquid's fill structure.
    If network is not provided, uses the current network context.
    """
    if network is None:
        network = get_current_network()
        
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO trades (
            trade_id, order_id, coin, side, price, size, fee, timestamp,
            closed_pnl, hash, crossed, start_position, dir, fee_token, builder_fee, network
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('tid'), trade_data.get('oid'), trade_data.get('coin'), trade_data.get('side'),
            trade_data.get('px'), trade_data.get('sz'), trade_data.get('fee'), trade_data.get('time'),
            trade_data.get('closedPnl'), trade_data.get('hash'), trade_data.get('crossed'),
            trade_data.get('startPosition'), trade_data.get('dir'), trade_data.get('feeToken'),
            trade_data.get('builderFee'), network
        ))
        print(f"[DBManager] Added trade for {trade_data.get('coin')} on {network}: {trade_data.get('dir')} {trade_data.get('sz')} @ {trade_data.get('px')}")

        # Update positions table
        update_position(cursor, trade_data, network)

        conn.commit()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"[DBManager] Trade with ID {trade_data.get('tid')} already exists on {network}. Skipping.")
        else:
            print(f"[DBManager] Error adding trade: {e}")
            raise
    except Exception as e:
        print(f"[DBManager] Unexpected error adding trade: {e}")
        conn.rollback() # Rollback on other errors
        raise
    finally:
        conn.close()

def update_position(cursor: sqlite3.Cursor, trade_data: dict, network: str = None):
    """
    Updates the net position for a coin based on a new trade.
    This is a simplified position update logic. More sophisticated logic might be needed
    for accurate PnL, average entry of mixed long/short, etc.
    Assumes trade_data contains 'coin', 'side', 'px' (price), 'sz' (size).
    If network is not provided, uses the current network context.
    """
    if network is None:
        network = get_current_network()
        
    coin = trade_data['coin']
    trade_price = float(trade_data['px'])
    trade_size = float(trade_data['sz'])
    trade_side = trade_data['side'] # 'B' for Buy, 'A' for Sell

    cursor.execute("SELECT net_size, average_entry_price, total_cost FROM positions WHERE coin = ? AND network = ?", (coin, network))
    row = cursor.fetchone()

    current_net_size = 0
    current_avg_entry = 0
    current_total_cost = 0

    if row:
        current_net_size = row['net_size']
        current_avg_entry = row['average_entry_price']
        current_total_cost = row['total_cost']

    new_net_size = current_net_size
    new_avg_entry = current_avg_entry
    new_total_cost = current_total_cost

    trade_value = trade_price * trade_size

    if trade_side == 'B': # Buy
        new_total_cost = current_total_cost + trade_value
        new_net_size = current_net_size + trade_size
        if new_net_size != 0: # Avoid division by zero if position closes to zero then reopens
            if current_net_size >= 0: # Was long or flat
                new_avg_entry = new_total_cost / new_net_size
            else: # Was short, now flipping or reducing short
                if new_net_size > 0: # Flipped to long
                    new_avg_entry = trade_price
                    new_total_cost = trade_price * new_net_size # Reset cost basis
                else: # Reducing short, avg_entry of short doesn't change with a buy-to-cover
                    new_avg_entry = current_avg_entry if current_net_size != 0 else 0

    elif trade_side == 'A': # Sell
        new_total_cost = current_total_cost - trade_value # Cost basis reduces for longs, or becomes more negative for shorts
        new_net_size = current_net_size - trade_size
        if new_net_size != 0:
            if current_net_size <= 0: # Was short or flat
                new_avg_entry = abs(new_total_cost / new_net_size) # Cost is negative for shorts
            else: # Was long, now flipping or reducing long
                if new_net_size < 0: # Flipped to short
                    new_avg_entry = trade_price
                    new_total_cost = -trade_price * abs(new_net_size) # Reset cost basis (negative for shorts)
                else: # Reducing long, avg_entry of long doesn't change with a sell-to-reduce
                     new_avg_entry = current_avg_entry if current_net_size != 0 else 0
    
    # If new_net_size becomes zero, reset avg_entry_price and total_cost
    if abs(new_net_size) < 1e-9: # Effectively zero
        new_avg_entry = 0
        new_total_cost = 0
        new_net_size = 0

    if row:
        cursor.execute('''
        UPDATE positions SET net_size = ?, average_entry_price = ?, total_cost = ?, last_updated = CURRENT_TIMESTAMP
        WHERE coin = ? AND network = ?
        ''', (new_net_size, new_avg_entry, new_total_cost, coin, network))
    else:
        cursor.execute('''
        INSERT INTO positions (coin, network, net_size, average_entry_price, total_cost, last_updated)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (coin, network, new_net_size, new_avg_entry, new_total_cost))

    print(f"[DBManager] Updated position for {coin} on {network}: Net Size: {new_net_size:.4f}, Avg Entry: {new_avg_entry:.2f}")

def get_current_positions(network: str = None):
    """Retrieves all current positions from the positions table for a specific network.
    If network is not provided, uses the current network context."""
    if network is None:
        network = get_current_network()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coin, net_size, average_entry_price, total_cost, last_updated FROM positions WHERE net_size != 0 AND network = ?", (network,))
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return positions

def get_all_trades(network: str = None):
    """Retrieves all trades from the trades table for a specific network.
    If network is not provided, uses the current network context."""
    if network is None:
        network = get_current_network()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades WHERE network = ? ORDER BY timestamp DESC", (network,))
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return trades

def add_open_order(order_details: dict, network: str = None):
    """
    Adds an order to the open_orders_tracking table.
    'order_details' should contain: order_id, symbol, side, order_type, price (optional), size, timestamp_placed.
    If network is not provided, uses the current network context.
    """
    if network is None:
        network = get_current_network()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO open_orders_tracking (order_id, symbol, side, order_type, price, size, network, timestamp_placed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_details['order_id'],
            order_details['symbol'],
            order_details['side'],
            order_details['order_type'],
            order_details.get('price'), # Optional, will be None if not present
            order_details['size'],
            network,
            order_details['timestamp_placed']
        ))
        conn.commit()
        print(f"[DBManager] Added to open_orders_tracking: Order ID {order_details['order_id']} for {order_details['symbol']} on {network}")
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"[DBManager] Order ID {order_details['order_id']} already in open_orders_tracking on {network}. Skipping.")
        else:
            print(f"[DBManager] Error adding to open_orders_tracking: {e}")
            # raise # Optionally re-raise
    except Exception as e:
        print(f"[DBManager] Unexpected error adding to open_orders_tracking: {e}")
        conn.rollback()
        # raise # Optionally re-raise
    finally:
        conn.close()

def remove_open_order(order_id: int, network: str = None):
    """
    Removes an order from the open_orders_tracking table, typically after it's filled or confirmed closed.
    If network is not provided, uses the current network context.
    """
    if network is None:
        network = get_current_network()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM open_orders_tracking WHERE order_id = ? AND network = ?", (order_id, network))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"[DBManager] Removed Order ID {order_id} from open_orders_tracking on {network}.")
        else:
            print(f"[DBManager] Order ID {order_id} not found in open_orders_tracking for removal on {network} (might have been removed already or never added).")
    except Exception as e:
        print(f"[DBManager] Error removing Order ID {order_id} from open_orders_tracking: {e}")
        conn.rollback()
        # raise # Optionally re-raise
    finally:
        conn.close()

def get_tracked_open_orders(network: str = None):
    """Retrieves all orders currently in the open_orders_tracking table for a specific network.
    If network is not provided, uses the current network context."""
    if network is None:
        network = get_current_network()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, symbol, side, order_type, price, size, timestamp_placed FROM open_orders_tracking WHERE network = ? ORDER BY timestamp_placed DESC", (network,))
    open_orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return open_orders

# Conversation history functions
def add_conversation_message(session_id: str, role: str, content: str, tool_calls: dict = None):
    """
    Adds a message to the conversation history.
    
    Args:
        session_id: Unique identifier for the conversation session
        role: 'user', 'assistant', or 'system'
        content: The message content
        tool_calls: Optional dict of tool calls made by the assistant
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    import json
    tool_calls_json = json.dumps(tool_calls) if tool_calls else None
    
    try:
        cursor.execute('''
        INSERT INTO conversations (session_id, role, content, tool_calls)
        VALUES (?, ?, ?, ?)
        ''', (session_id, role, content, tool_calls_json))
        conn.commit()
        print(f"[DBManager] Added {role} message to conversation {session_id[:8]}...")
    except Exception as e:
        print(f"[DBManager] Error adding conversation message: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_conversation_history(session_id: str, limit: int = 50):
    """
    Retrieves conversation history for a given session.
    
    Args:
        session_id: Unique identifier for the conversation session
        limit: Maximum number of messages to retrieve (default: 50)
    
    Returns:
        List of message dictionaries ordered by timestamp
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT role, content, tool_calls, timestamp 
    FROM conversations 
    WHERE session_id = ? 
    ORDER BY timestamp DESC 
    LIMIT ?
    ''', (session_id, limit))
    
    messages = []
    for row in cursor.fetchall():
        msg = dict(row)
        # Parse tool_calls JSON if present
        if msg['tool_calls']:
            import json
            try:
                msg['tool_calls'] = json.loads(msg['tool_calls'])
            except:
                msg['tool_calls'] = None
        messages.append(msg)
    
    conn.close()
    
    # Reverse to get chronological order
    return list(reversed(messages))

def get_all_sessions():
    """
    Retrieves all unique session IDs with their message counts and last activity.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        session_id,
        COUNT(*) as message_count,
        MAX(timestamp) as last_activity,
        MIN(timestamp) as first_activity
    FROM conversations
    GROUP BY session_id
    ORDER BY last_activity DESC
    ''')
    
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def clear_session_history(session_id: str):
    """
    Deletes all messages for a given session.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"[DBManager] Cleared {deleted_count} messages from session {session_id[:8]}...")
        return deleted_count
    except Exception as e:
        print(f"[DBManager] Error clearing session history: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

class DBManager:
    """Database Manager class that wraps all database operations."""
    
    def __init__(self):
        """Initialize the database manager and ensure tables exist."""
        initialize_database()
    
    def add_trade(self, trade_data: dict, network: str = None):
        """Add a trade to the database."""
        return add_trade(trade_data, network)
    
    def get_current_positions(self, network: str = None):
        """Get all current positions."""
        return get_current_positions(network)
    
    def get_all_trades(self, network: str = None):
        """Get all trades."""
        return get_all_trades(network)
    
    def add_open_order(self, order_details: dict, network: str = None):
        """Add an open order to tracking."""
        return add_open_order(order_details, network)
    
    def remove_open_order(self, order_id: int, network: str = None):
        """Remove an open order from tracking."""
        return remove_open_order(order_id, network)
    
    def get_tracked_open_orders(self, network: str = None):
        """Get all tracked open orders."""
        return get_tracked_open_orders(network)
    
    def add_conversation_message(self, session_id: str, role: str, content: str, tool_calls: dict = None):
        """Add a message to conversation history."""
        return add_conversation_message(session_id, role, content, tool_calls)
    
    def get_conversation_history(self, session_id: str, limit: int = 50):
        """Get conversation history for a session."""
        return get_conversation_history(session_id, limit)
    
    def get_all_sessions(self):
        """Get all conversation sessions."""
        return get_all_sessions()
    
    def clear_session_history(self, session_id: str):
        """Clear history for a session."""
        return clear_session_history(session_id)
    
    def generate_session_id(self):
        """Generate a new session ID."""
        import uuid
        return str(uuid.uuid4())


if __name__ == '__main__':
    # Example usage:
    print("Initializing database...")
    initialize_database()
    print("\nDatabase initialized.")

    # Example trade data (replace with actual data from Hyperliquid)
    mock_fill_1 = {
        "tid": 1234567890, "oid": 98765, "coin": "BTC", "side": "B", "px": "50000.0", "sz": "0.1",
        "fee": "2.5", "time": int(datetime.now().timestamp() * 1000), "closedPnl": "0.0",
        "hash": "0xabc123", "crossed": True, "startPosition": "0.0", "dir": "Open Long",
        "feeToken": "USDC", "builderFee": "0.1"
    }
    mock_fill_2 = {
        "tid": 1234567891, "oid": 98766, "coin": "BTC", "side": "B", "px": "50500.0", "sz": "0.05",
        "fee": "1.25", "time": int(datetime.now().timestamp() * 1000) + 1000, "closedPnl": "0.0",
        "hash": "0xdef456", "crossed": True, "startPosition": "0.1", "dir": "Open Long",
        "feeToken": "USDC", "builderFee": "0.05"
    }
    mock_fill_3 = { # Selling a part of the BTC position
        "tid": 1234567892, "oid": 98767, "coin": "BTC", "side": "A", "px": "51000.0", "sz": "0.05",
        "fee": "1.20", "time": int(datetime.now().timestamp() * 1000) + 2000, "closedPnl": "25.0", # (51000-50000)*0.05 = 50, but simplified PNL
        "hash": "0xghi789", "crossed": True, "startPosition": "0.15", "dir": "Close Long",
        "feeToken": "USDC", "builderFee": "0.05"
    }
    mock_fill_4 = { # Opening a new short position for ETH
        "tid": 2234567890, "oid": 88765, "coin": "ETH", "side": "A", "px": "4000.0", "sz": "1.0",
        "fee": "4.0", "time": int(datetime.now().timestamp() * 1000) + 3000, "closedPnl": "0.0",
        "hash": "0xjkl012", "crossed": True, "startPosition": "0.0", "dir": "Open Short",
        "feeToken": "USDC", "builderFee": "0.2"
    }

    print("\nAdding trades...")
    add_trade(mock_fill_1)
    add_trade(mock_fill_2)
    add_trade(mock_fill_3)
    add_trade(mock_fill_4)

    print("\nCurrent Positions:")
    positions = get_current_positions()
    if positions:
        for pos in positions:
            print(f"  Coin: {pos['coin']}, Net Size: {pos['net_size']:.4f}, Avg Entry: {pos['average_entry_price']:.2f}, Total Cost: {pos['total_cost']:.2f}")
    else:
        print("  No open positions.")

    print("\nAll Trades:")
    all_trades = get_all_trades()
    if all_trades:
        for t in all_trades[:3]: # Print a few recent trades
             print(f"  Trade ID: {t['trade_id']}, Coin: {t['coin']}, Dir: {t['dir']}, Size: {t['size']}, Px: {t['price']}, Time: {t['timestamp']}")
    else:
        print("  No trades recorded.")

    print("\nTesting open_orders_tracking...")
    mock_open_order = {
        "order_id": 999001, "symbol": "ETH", "side": "B", "order_type": "limit", 
        "price": 3000.0, "size": 0.5, "timestamp_placed": int(datetime.now().timestamp() * 1000)
    }
    add_open_order(mock_open_order)
    tracked_orders = get_tracked_open_orders()
    print("  Currently tracked open orders:", tracked_orders)
    remove_open_order(999001)
    tracked_orders_after_removal = get_tracked_open_orders()
    print("  Tracked open orders after removal:", tracked_orders_after_removal)

    # Test duplicate trade
    print("\nAttempting to add duplicate trade (should be skipped):")
    add_trade(mock_fill_1) 