"""
ub370uc774ud130ubca0uc774uc2a4 uad00ub9ac ubaa8ub4c8: uc7a1uc740 ub370uc774ud130ub97c uc800uc7a5ud558uace0 uad00ub9acud558ub294 ud074ub798uc2a4ub97c uc815uc758ud569ub2c8ub2e4.
"""

import sqlite3
import json
from datetime import datetime
import os
from config.config import DB_NAME


class DatabaseManager:
    """ub370uc774ud130ubca0uc774uc2a4 uad00ub9ac ud074ub798uc2a4"""
    
    def __init__(self, db_name=None):
        """
        DatabaseManager ud074ub798uc2a4 ucd08uae30ud654
        
        Args:
            db_name (str, optional): ub370uc774ud130ubca0uc774uc2a4 ud30cuc77c uc774ub984
        """
        self.db_name = db_name or DB_NAME
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """
        ub370uc774ud130ubca0uc774uc2a4uc5d0 uc5f0uacb0
        """
        try:
            # ud604uc7ac uc2a4ud06cub9bdud2b8 uacbdub85cub97c uae30uc900uc73cub85c DB ud30cuc77c uacbdub85c uc124uc815
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.db_name)
            self.conn = sqlite3.connect(db_path)
            # uacb0uacfcuac12uc744 ub514uc154ub108ub9acub85c ubc1bub3c4ub85d uc124uc815
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"ub370uc774ud130ubca0uc774uc2a4 uc5f0uacb0 uc624ub958: {e}")
    
    def _create_tables(self):
        """
        ud544uc694ud55c ud14cuc774ube14 uc0dduc131
        """
        try:
            # API ud1a0ud070 ud14cuc774ube14
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_type TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    expires_at DATETIME NOT NULL
                )
            ''')
            
            # ud2b8ub808uc774ub529 uc138uc158 ud14cuc774ube14
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    strategy TEXT,
                    buy_price REAL,
                    buy_volume REAL,
                    buy_amount REAL,
                    buy_time DATETIME,
                    sell_price REAL,
                    sell_volume REAL,
                    sell_amount REAL,
                    sell_time DATETIME,
                    profit_loss REAL,
                    profit_loss_percent REAL,
                    status TEXT DEFAULT 'open',
                    order_id TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # uac00uaca9 ub370uc774ud130 ud14cuc774ube14
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume REAL,
                    UNIQUE(ticker, timestamp)
                )
            ''')
            
            # ud2b8ub808uc774ub529 uc804ub7b5 ud14cuc774ube14
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    parameters TEXT,  -- JSON ud615ud0dcub85c uc800uc7a5
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ud2b8ub808uc774ub529 ub85cuadf8 ud14cuc774ube14
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,  -- JSON ud615ud0dcub85c uc800uc7a5
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"ud14cuc774ube14 uc0dduc131 uc624ub958: {e}")
    
    def save_token(self, token_type, access_token, expires_at):
        """
        API ud1a0ud070 uc800uc7a5
        
        Args:
            token_type (str): ud1a0ud070 uc720ud615
            access_token (str): uc561uc138uc2a4 ud1a0ud070
            expires_at (datetime): ub9ccub8cc uc2dcuac04
        """
        try:
            # uae30uc874 ud1a0ud070 uc0aduc81c
            self.cursor.execute(
                "DELETE FROM api_tokens WHERE token_type = ?",
                (token_type,)
            )
            
            # uc0c8 ud1a0ud070 uc800uc7a5
            self.cursor.execute(
                "INSERT INTO api_tokens (token_type, access_token, expires_at) VALUES (?, ?, ?)",
                (token_type, access_token, expires_at)
            )
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"ud1a0ud070 uc800uc7a5 uc624ub958: {e}")
    
    def get_token(self, token_type):
        """
        uc800uc7a5ub41c API ud1a0ud070 uac00uc838uc624uae30
        
        Args:
            token_type (str): ud1a0ud070 uc720ud615
            
        Returns:
            tuple: (access_token, expires_at) ub610ub294 (None, None)
        """
        try:
            self.cursor.execute(
                "SELECT access_token, expires_at FROM api_tokens WHERE token_type = ?",
                (token_type,)
            )
            result = self.cursor.fetchone()
            
            if result:
                # sqlite3.Row ub97c ud29cud50cub85c ubcc0ud658
                access_token = result['access_token']
                expires_at = datetime.fromisoformat(result['expires_at'])
                return access_token, expires_at
            
            return None, None
        except sqlite3.Error as e:
            print(f"ud1a0ud070 uc870ud68c uc624ub958: {e}")
            return None, None
    
    def save_trading_session(self, ticker, strategy=None, buy_price=None, buy_volume=None, buy_amount=None, 
                          buy_time=None, order_id=None, notes=None):
        """
        uc0c8ub85cuc6b4 ud2b8ub808uc774ub529 uc138uc158 uc800uc7a5
        
        Args:
            ticker (str): ucf54uc778 ud2f0ucee4
            strategy (str, optional): uc0acuc6a9ub41c uc804ub7b5 uc774ub984
            buy_price (float, optional): ub9e4uc218 uac00uaca9
            buy_volume (float, optional): ub9e4uc218 uc218ub7c9
            buy_amount (float, optional): ub9e4uc218 uae08uc561
            buy_time (datetime, optional): ub9e4uc218 uc2dcuac04
            order_id (str, optional): uc8fcubb38 ID
            notes (str, optional): uba54ubaa8
            
        Returns:
            int: uc0dduc131ub41c uc138uc158 ID
        """
        try:
            buy_time_str = buy_time.isoformat() if buy_time else datetime.now().isoformat()
            
            self.cursor.execute(
                '''
                INSERT INTO trading_sessions (
                    ticker, strategy, buy_price, buy_volume, buy_amount, buy_time, order_id, notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (ticker, strategy, buy_price, buy_volume, buy_amount, buy_time_str, order_id, notes, 'open')
            )
            
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"ud2b8ub808uc774ub529 uc138uc158 uc800uc7a5 uc624ub958: {e}")
            return None
    
    def update_trading_session(self, session_id, sell_price=None, sell_volume=None, sell_amount=None,
                               sell_time=None, profit_loss=None, profit_loss_percent=None, status=None, notes=None):
        """
        ud2b8ub808uc774ub529 uc138uc158 uc5c5ub370uc774ud2b8 (ub9e4ub3c4 uc815ubcf4 ucd94uac00)
        
        Args:
            session_id (int): uc138uc158 ID
            sell_price (float, optional): ub9e4ub3c4 uac00uaca9
            sell_volume (float, optional): ub9e4ub3c4 uc218ub7c9
            sell_amount (float, optional): ub9e4ub3c4 uae08uc561
            sell_time (datetime, optional): ub9e4ub3c4 uc2dcuac04
            profit_loss (float, optional): uc218uc775/uc190uc2e4uc561
            profit_loss_percent (float, optional): uc218uc775/uc190uc2e4ub960
            status (str, optional): uc0c8ub85cuc6b4 uc0c1ud0dc ('open', 'closed', 'cancelled')
            notes (str, optional): ucd94uac00 uba54ubaa8
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        try:
            # uc5c5ub370uc774ud2b8ud560 ud544ub4dcuc640 uac12 ucee8uc2a4ud2b8ub7edud2b8
            update_fields = []
            values = []
            
            if sell_price is not None:
                update_fields.append("sell_price = ?")
                values.append(sell_price)
                
            if sell_volume is not None:
                update_fields.append("sell_volume = ?")
                values.append(sell_volume)
                
            if sell_amount is not None:
                update_fields.append("sell_amount = ?")
                values.append(sell_amount)
                
            if sell_time is not None:
                update_fields.append("sell_time = ?")
                values.append(sell_time.isoformat() if isinstance(sell_time, datetime) else sell_time)
                
            if profit_loss is not None:
                update_fields.append("profit_loss = ?")
                values.append(profit_loss)
                
            if profit_loss_percent is not None:
                update_fields.append("profit_loss_percent = ?")
                values.append(profit_loss_percent)
                
            if status is not None:
                update_fields.append("status = ?")
                values.append(status)
                
            if notes is not None:
                update_fields.append("notes = ?")
                values.append(notes)
            
            # uc5c5ub370uc774ud2b8ud560 ud544ub4dcuac00 uc5c6uc73cuba74 uc885ub8cc
            if not update_fields:
                return True
            
            # uc5c5ub370uc774ud2b8 ucffcub9ac uc791uc131
            query = f"UPDATE trading_sessions SET {', '.join(update_fields)} WHERE id = ?"
            values.append(session_id)
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            return True
        except sqlite3.Error as e:
            print(f"ud2b8ub808uc774ub529 uc138uc158 uc5c5ub370uc774ud2b8 uc624ub958: {e}")
            return False
    
    def get_trading_session(self, session_id):
        """
        ud2b8ub808uc774ub529 uc138uc158 uc870ud68c
        
        Args:
            session_id (int): uc138uc158 ID
            
        Returns:
            dict: uc138uc158 uc815ubcf4
        """
        try:
            self.cursor.execute("SELECT * FROM trading_sessions WHERE id = ?", (session_id,))
            row = self.cursor.fetchone()
            
            if row:
                # sqlite3.Rowub97c ub514uc154ub108ub9acub85c ubcc0ud658
                return dict(row)
            
            return None
        except sqlite3.Error as e:
            print(f"ud2b8ub808uc774ub529 uc138uc158 uc870ud68c uc624ub958: {e}")
            return None
    
    def get_open_trading_sessions(self):
        """
        ud604uc7ac uc5f4ub824uc788ub294(ub9e4ub3c4ub418uc9c0 uc54auc740) uc138uc158 ubaa9ub85d uc870ud68c
        
        Returns:
            list: uc5f4ub824uc788ub294 uc138uc158 ubaa9ub85d
        """
        try:
            self.cursor.execute("SELECT * FROM trading_sessions WHERE status = 'open' ORDER BY buy_time DESC")
            rows = self.cursor.fetchall()
            
            # sqlite3.Row ubaa9ub85duc744 ub514uc154ub108ub9ac ubaa9ub85duc73cub85c ubcc0ud658
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"uc5f4ub824uc788ub294 uc138uc158 uc870ud68c uc624ub958: {e}")
            return []
    
    def save_price_data(self, ticker, timestamp, open_price, high_price, low_price, close_price, volume):
        """
        uac00uaca9 ub370uc774ud130 uc800uc7a5
        
        Args:
            ticker (str): ucf54uc778 ud2f0ucee4
            timestamp (datetime): uc2dcuac04
            open_price (float): uc2dcuac00
            high_price (float): uace0uac00
            low_price (float): uc800uac00
            close_price (float): uc885uac00
            volume (float): uac70ub798ub7c9
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        try:
            timestamp_str = timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
            
            # UNIQUE uc81cuc57duc870uac74uc744 uace0ub824ud558uc5ec REPLACE uc0acuc6a9
            self.cursor.execute(
                '''
                INSERT OR REPLACE INTO price_data (
                    ticker, timestamp, open_price, high_price, low_price, close_price, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (ticker, timestamp_str, open_price, high_price, low_price, close_price, volume)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"uac00uaca9 ub370uc774ud130 uc800uc7a5 uc624ub958: {e}")
            return False
    
    def get_price_data(self, ticker, start_time=None, end_time=None, limit=100):
        """
        uc800uc7a5ub41c uac00uaca9 ub370uc774ud130 uc870ud68c
        
        Args:
            ticker (str): ucf54uc778 ud2f0ucee4
            start_time (datetime, optional): uc2dcuc791 uc2dcuac04
            end_time (datetime, optional): uc885ub8cc uc2dcuac04
            limit (int): ucd5cub300 uac1cuc218
            
        Returns:
            list: uac00uaca9 ub370uc774ud130 ubaa9ub85d
        """
        try:
            query = "SELECT * FROM price_data WHERE ticker = ?"
            params = [ticker]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat() if isinstance(start_time, datetime) else start_time)
                
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat() if isinstance(end_time, datetime) else end_time)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"uac00uaca9 ub370uc774ud130 uc870ud68c uc624ub958: {e}")
            return []
    
    def save_trading_log(self, log_type, message, data=None):
        """
        ud2b8ub808uc774ub529 ub85cuadf8 uc800uc7a5
        
        Args:
            log_type (str): ub85cuadf8 uc720ud615 ('INFO', 'WARNING', 'ERROR')
            message (str): ub85cuadf8 uba54uc2dcuc9c0
            data (dict, optional): ucd94uac00 ub370uc774ud130
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        try:
            data_json = json.dumps(data) if data else None
            
            self.cursor.execute(
                "INSERT INTO trading_logs (log_type, message, data) VALUES (?, ?, ?)",
                (log_type, message, data_json)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"ub85cuadf8 uc800uc7a5 uc624ub958: {e}")
            return False
    
    def close(self):
        """
        ub370uc774ud130ubca0uc774uc2a4 uc5f0uacb0 ub2ebuae30
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
