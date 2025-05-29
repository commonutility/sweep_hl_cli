"""
Database migration script to add network support.
This script updates the existing database schema to support mainnet/testnet separation.
"""

import sqlite3
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.hyperliquid_wrapper.database_handlers.database_manager import DATABASE_NAME, get_db_connection

def migrate_database():
    """Migrate the database to support network separation."""
    print("Starting database migration...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed by checking if network column exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'network' in columns:
            print("Database already migrated. Network column exists in trades table.")
            return
        
        print("Migrating database schema...")
        
        # 1. Create new tables with network support
        print("Creating new tables with network support...")
        
        # Create new trades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER,
            order_id INTEGER,
            coin TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            fee REAL,
            timestamp INTEGER NOT NULL,
            closed_pnl REAL,
            hash TEXT,
            crossed BOOLEAN,
            start_position TEXT,
            dir TEXT,
            fee_token TEXT,
            builder_fee REAL,
            network TEXT NOT NULL DEFAULT 'testnet',
            received_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(trade_id, network)
        )
        ''')
        
        # Create new positions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions_new (
            coin TEXT NOT NULL,
            network TEXT NOT NULL DEFAULT 'testnet',
            net_size REAL NOT NULL DEFAULT 0,
            average_entry_price REAL NOT NULL DEFAULT 0,
            total_cost REAL NOT NULL DEFAULT 0,
            unrealized_pnl REAL DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (coin, network)
        )
        ''')
        
        # Create new open_orders_tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS open_orders_tracking_new (
            internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            order_type TEXT NOT NULL,
            price REAL,
            size REAL NOT NULL,
            network TEXT NOT NULL DEFAULT 'testnet',
            timestamp_placed INTEGER NOT NULL,
            UNIQUE(order_id, network)
        )
        ''')
        
        # 2. Copy existing data to new tables (defaulting to testnet)
        print("Copying existing data to new tables (defaulting to testnet)...")
        
        # Copy trades
        cursor.execute('''
        INSERT INTO trades_new (
            id, trade_id, order_id, coin, side, price, size, fee, timestamp,
            closed_pnl, hash, crossed, start_position, dir, fee_token, builder_fee,
            network, received_at
        )
        SELECT 
            id, trade_id, order_id, coin, side, price, size, fee, timestamp,
            closed_pnl, hash, crossed, start_position, dir, fee_token, builder_fee,
            'testnet', received_at
        FROM trades
        ''')
        
        # Copy positions
        cursor.execute('''
        INSERT INTO positions_new (coin, network, net_size, average_entry_price, total_cost, unrealized_pnl, last_updated)
        SELECT coin, 'testnet', net_size, average_entry_price, total_cost, unrealized_pnl, last_updated
        FROM positions
        ''')
        
        # Copy open orders
        cursor.execute('''
        INSERT INTO open_orders_tracking_new (
            internal_id, order_id, symbol, side, order_type, price, size, network, timestamp_placed
        )
        SELECT 
            internal_id, order_id, symbol, side, order_type, price, size, 'testnet', timestamp_placed
        FROM open_orders_tracking
        ''')
        
        # 3. Drop old tables
        print("Dropping old tables...")
        cursor.execute("DROP TABLE trades")
        cursor.execute("DROP TABLE positions")
        cursor.execute("DROP TABLE open_orders_tracking")
        
        # 4. Rename new tables
        print("Renaming new tables...")
        cursor.execute("ALTER TABLE trades_new RENAME TO trades")
        cursor.execute("ALTER TABLE positions_new RENAME TO positions")
        cursor.execute("ALTER TABLE open_orders_tracking_new RENAME TO open_orders_tracking")
        
        # 5. Create indexes
        print("Creating indexes...")
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
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 