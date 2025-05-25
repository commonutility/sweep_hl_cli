import sqlite3
import os
from datetime import datetime

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

    # Create trades table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER UNIQUE,       -- Hyperliquid's unique trade ID (tid)
        order_id INTEGER,              -- Hyperliquid's order ID (oid)
        coin TEXT NOT NULL,
        side TEXT NOT NULL,            -- 'B' (Buy) or 'A' (Sell)
        price REAL NOT NULL,
        size REAL NOT NULL,
        fee REAL,
        timestamp INTEGER NOT NULL,    -- Unix timestamp in milliseconds
        closed_pnl REAL,
        hash TEXT,
        crossed BOOLEAN,
        start_position TEXT,
        dir TEXT,                      -- 'Open Long', 'Close Long', 'Open Short', 'Close Short'
        fee_token TEXT,
        builder_fee REAL,
        received_at TEXT DEFAULT CURRENT_TIMESTAMP -- When the fill was processed by our system
    )
    ''')
    print("[DBManager] 'trades' table initialized or already exists.")

    # Create positions table
    # This table will store the current net position for each coin.
    # It will be updated after each trade.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        coin TEXT PRIMARY KEY,
        net_size REAL NOT NULL DEFAULT 0,
        average_entry_price REAL NOT NULL DEFAULT 0, -- Weighted average entry price
        total_cost REAL NOT NULL DEFAULT 0,          -- Total cost basis for the current position
        unrealized_pnl REAL DEFAULT 0,               -- Will require external price updates to calculate accurately
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("[DBManager] 'positions' table initialized or already exists.")

    conn.commit()
    conn.close()
    print("[DBManager] Database initialization complete.")

def add_trade(trade_data: dict):
    """
    Adds a trade fill to the trades table and updates the positions table.
    'trade_data' is expected to be a dictionary matching Hyperliquid's fill structure.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO trades (
            trade_id, order_id, coin, side, price, size, fee, timestamp,
            closed_pnl, hash, crossed, start_position, dir, fee_token, builder_fee
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('tid'), trade_data.get('oid'), trade_data.get('coin'), trade_data.get('side'),
            trade_data.get('px'), trade_data.get('sz'), trade_data.get('fee'), trade_data.get('time'),
            trade_data.get('closedPnl'), trade_data.get('hash'), trade_data.get('crossed'),
            trade_data.get('startPosition'), trade_data.get('dir'), trade_data.get('feeToken'),
            trade_data.get('builderFee')
        ))
        print(f"[DBManager] Added trade for {trade_data.get('coin')}: {trade_data.get('dir')} {trade_data.get('sz')} @ {trade_data.get('px')}")

        # Update positions table
        update_position(cursor, trade_data)

        conn.commit()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: trades.trade_id" in str(e):
            print(f"[DBManager] Trade with ID {trade_data.get('tid')} already exists. Skipping.")
        else:
            print(f"[DBManager] Error adding trade: {e}")
            raise
    except Exception as e:
        print(f"[DBManager] Unexpected error adding trade: {e}")
        conn.rollback() # Rollback on other errors
        raise
    finally:
        conn.close()

def update_position(cursor: sqlite3.Cursor, trade_data: dict):
    """
    Updates the net position for a coin based on a new trade.
    This is a simplified position update logic. More sophisticated logic might be needed
    for accurate PnL, average entry of mixed long/short, etc.
    Assumes trade_data contains 'coin', 'side', 'px' (price), 'sz' (size).
    """
    coin = trade_data['coin']
    trade_price = float(trade_data['px'])
    trade_size = float(trade_data['sz'])
    trade_side = trade_data['side'] # 'B' for Buy, 'A' for Sell

    cursor.execute("SELECT net_size, average_entry_price, total_cost FROM positions WHERE coin = ?", (coin,))
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
        WHERE coin = ?
        ''', (new_net_size, new_avg_entry, new_total_cost, coin))
    else:
        cursor.execute('''
        INSERT INTO positions (coin, net_size, average_entry_price, total_cost, last_updated)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (coin, new_net_size, new_avg_entry, new_total_cost))

    print(f"[DBManager] Updated position for {coin}: Net Size: {new_net_size:.4f}, Avg Entry: {new_avg_entry:.2f}")

def get_current_positions():
    """Retrieves all current positions from the positions table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coin, net_size, average_entry_price, total_cost, last_updated FROM positions WHERE net_size != 0")
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return positions

def get_all_trades():
    """Retrieves all trades from the trades table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC")
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return trades

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

    # Test duplicate trade
    print("\nAttempting to add duplicate trade (should be skipped):")
    add_trade(mock_fill_1) 