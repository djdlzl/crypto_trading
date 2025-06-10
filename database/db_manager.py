"""데이터베이스 관리 모듈

MariaDB를 사용하여 업비트 API 인증 토큰 및 거래 데이터를 관리합니다.
"""
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from config.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


class DatabaseManager:
    """데이터베이스 연결 및 쿼리 실행을 관리하는 클래스"""

    def __init__(self):
        """DatabaseManager 클래스 인스턴스 초기화"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                # 필요한 테이블 생성
                self._create_tables()
        except Error as e:
            logging.error(f"데이터베이스 연결 오류: {e}")
            self.connection = None
            self.cursor = None

    def _create_tables(self):
        """필요한 테이블 생성"""
        try:
            # 토큰 테이블 생성 - 업비트 API 인증 토큰 저장용
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token_type VARCHAR(50) NOT NULL,
                access_token TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 웹소켓 인증 정보 테이블 생성 - 업비트 웹소켓 인증 정보 저장용
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS websocket_auth (
                id INT AUTO_INCREMENT PRIMARY KEY,
                auth_type VARCHAR(50) NOT NULL,
                auth_token TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 암호화폐 거래 내역 테이블 생성
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_trades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                market VARCHAR(20) NOT NULL,
                uuid VARCHAR(50) UNIQUE NOT NULL,
                side VARCHAR(10) NOT NULL,
                price DECIMAL(20, 8) NOT NULL,
                volume DECIMAL(20, 8) NOT NULL,
                executed_volume DECIMAL(20, 8) NOT NULL,
                executed_price DECIMAL(20, 8) NOT NULL,
                order_state VARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL,
                trade_timestamp DATETIME NOT NULL
            )
            """)
            
            # 계좌 잔고 테이블 생성
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_balances (
                id INT AUTO_INCREMENT PRIMARY KEY,
                currency VARCHAR(20) NOT NULL,
                balance DECIMAL(20, 8) NOT NULL,
                locked DECIMAL(20, 8) NOT NULL,
                avg_buy_price DECIMAL(20, 8) NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_currency (currency)
            )
            """)
            
            self.connection.commit()
        except Error as e:
            logging.error(f"테이블 생성 오류: {e}")
            
    def save_token(self, token_type, access_token, expires_at):
        """
        API 액세스 토큰을 저장합니다.
        
        Args:
            token_type (str): 토큰 유형
            access_token (str): 액세스 토큰
            expires_at (datetime): 토큰 만료 시간
        
        Returns:
            bool: 성공 여부
        """
        try:
            if self.connection is None or not self.connection.is_connected():
                self.__init__()
                
            # 기존 같은 유형의 토큰 삭제
            self.cursor.execute(
                "DELETE FROM access_tokens WHERE token_type = %s",
                (token_type,)
            )
            
            # 새 토큰 저장
            self.cursor.execute(
                """
                INSERT INTO access_tokens (token_type, access_token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (token_type, access_token, expires_at)
            )
            
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"토큰 저장 오류: {e}")
            return False
            
    def get_token(self, token_type):
        """
        저장된 액세스 토큰을 조회합니다.
        
        Args:
            token_type (str): 토큰 유형
        
        Returns:
            tuple: (액세스 토큰, 만료 시간) 또는 토큰이 없는 경우 (None, None)
        """
        try:
            if self.connection is None or not self.connection.is_connected():
                self.__init__()
                
            self.cursor.execute(
                "SELECT access_token, expires_at FROM access_tokens WHERE token_type = %s",
                (token_type,)
            )
            
            result = self.cursor.fetchone()
            if result:
                return result['access_token'], result['expires_at']
            return None, None
        except Error as e:
            logging.error(f"토큰 조회 오류: {e}")
            return None, None
            
    def save_auth(self, auth_type, auth_token, expires_at):
        """
        웹소켓 인증 정보를 저장합니다.
        
        Args:
            auth_type (str): 인증 유형
            auth_token (str): 인증 토큰
            expires_at (datetime): 인증 만료 시간
        
        Returns:
            bool: 성공 여부
        """
        try:
            if self.connection is None or not self.connection.is_connected():
                self.__init__()
                
            # 기존 같은 유형의 인증 정보 삭제
            self.cursor.execute(
                "DELETE FROM websocket_auth WHERE auth_type = %s",
                (auth_type,)
            )
            
            # 새 인증 정보 저장
            self.cursor.execute(
                """
                INSERT INTO websocket_auth (auth_type, auth_token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (auth_type, auth_token, expires_at)
            )
            
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"인증 정보 저장 오류: {e}")
            return False
            
    def get_auth(self, auth_type):
        """
        저장된 웹소켓 인증 정보를 조회합니다.
        
        Args:
            auth_type (str): 인증 유형
        
        Returns:
            tuple: (인증 토큰, 만료 시간) 또는 인증 정보가 없는 경우 (None, None)
        """
        try:
            if self.connection is None or not self.connection.is_connected():
                self.__init__()
                
            self.cursor.execute(
                "SELECT auth_token, expires_at FROM websocket_auth WHERE auth_type = %s",
                (auth_type,)
            )
            
            result = self.cursor.fetchone()
            if result:
                return result['auth_token'], result['expires_at']
            return None, None
        except Error as e:
            logging.error(f"인증 정보 조회 오류: {e}")
            return None, None
            
    def save_trade(self, trade_data):
        """
        거래 내역을 저장합니다.
        
        Args:
            trade_data (dict): 거래 데이터
        
        Returns:
            bool: 성공 여부
        """
        try:
            if self.connection is None or not self.connection.is_connected():
                self.__init__()
            
            self.cursor.execute(
                """
                INSERT INTO crypto_trades (
                    market, uuid, side, price, volume, 
                    executed_volume, executed_price, order_state, 
                    created_at, trade_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    executed_volume = VALUES(executed_volume),
                    executed_price = VALUES(executed_price),
                    order_state = VALUES(order_state),
                    trade_timestamp = VALUES(trade_timestamp)
                """,
                (
                    trade_data['market'], trade_data['uuid'], trade_data['side'], 
                    trade_data['price'], trade_data['volume'], trade_data['executed_volume'],
                    trade_data['executed_price'], trade_data['order_state'],
                    trade_data['created_at'], trade_data['trade_timestamp']
                )
            )
            
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"거래 내역 저장 오류: {e}")
            return False
            
    def update_balance(self, balance_data):
        """
        계좌 잔고를 업데이트합니다.
        
        Args:
            balance_data (dict): 잔고 데이터
        
        Returns:
            bool: 성공 여부
        """
        try:
            if self.connection is None or not self.connection.is_connected():
                self.__init__()
                
            self.cursor.execute(
                """
                INSERT INTO account_balances (
                    currency, balance, locked, avg_buy_price, updated_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    balance = VALUES(balance),
                    locked = VALUES(locked),
                    avg_buy_price = VALUES(avg_buy_price),
                    updated_at = NOW()
                """,
                (
                    balance_data['currency'], balance_data['balance'],
                    balance_data['locked'], balance_data['avg_buy_price']
                )
            )
            
            self.connection.commit()
            return True
        except Error as e:
            logging.error(f"잔고 업데이트 오류: {e}")
            return False
            
    def close(self):
        """데이터베이스 연결을 닫습니다."""
        try:
            if self.connection and self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
        except Error as e:
            logging.error(f"데이터베이스 연결 종료 오류: {e}")