"""
업비트 트레이딩 봇 메인 모듈: 스케줄러를 사용하여 주기적으로 트레이딩 작업을 실행합니다.
"""

import sys
import time
import signal
import threading
from datetime import datetime, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from api.upbit_api import UpbitAPI
from database.db_manager import DatabaseManager
from trading.trading_logic import TradingLogic
from utils.logger import Logger
from utils.notification import Notifier
from config.condition import (
    TRADING_START_HOUR, TRADING_END_HOUR, MARKET_CHECK_INTERVAL,
    TRADE_INTERVAL, ORDER_CHECK_INTERVAL
)


class TradingBot:
    """
    암호화폐 트레이딩 봇 클래스
    주기적인 트레이딩 작업 스케줄링 및 실행을 담당합니다.
    """
    
    def __init__(self):
        """
        TradingBot 클래스 초기화
        """
        self.logger = Logger()
        self.notifier = Notifier()
        self.db_manager = DatabaseManager()
        self.api = UpbitAPI()
        self.trading_logic = TradingLogic(self.api, self.db_manager)
        
        # 스케줄러 초기화
        self.scheduler = BackgroundScheduler()
        self.running = False
        self.lock = threading.Lock()
        
        # 종료 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """
        종료 시그널 처리
        """
        self.logger.info("종료 신호를 받았습니다. 안전하게 종료합니다...")
        self.stop()
        sys.exit(0)
    
    def is_trading_hours(self):
        """
        현재 트레이딩 시간인지 확인
        
        Returns:
            bool: 트레이딩 시간 여부
        """
        now = datetime.now()
        current_hour = now.hour
        
        # 24시간 트레이딩
        if TRADING_START_HOUR is None or TRADING_END_HOUR is None:
            return True
        
        # 시작 시간이 종료 시간보다 큰 경우 (예: 22시 ~ 6시)
        if TRADING_START_HOUR > TRADING_END_HOUR:
            return current_hour >= TRADING_START_HOUR or current_hour < TRADING_END_HOUR
        
        # 일반적인 경우 (예: 9시 ~ 18시)
        return TRADING_START_HOUR <= current_hour < TRADING_END_HOUR
    
    def schedule_jobs(self):
        """
        작업 스케줄링
        """
        # 트레이딩 사이클 실행 (매수 신호 확인 및 주문)
        self.scheduler.add_job(
            self.execute_trade_cycle,
            IntervalTrigger(minutes=TRADE_INTERVAL),
            id='trade_cycle',
            replace_existing=True
        )
        
        # 매도 신호 확인
        self.scheduler.add_job(
            self.check_sell_signals,
            IntervalTrigger(minutes=TRADE_INTERVAL),
            id='sell_signals',
            replace_existing=True
        )
        
        # 미체결 주문 처리
        self.scheduler.add_job(
            self.handle_unfilled_orders,
            IntervalTrigger(minutes=ORDER_CHECK_INTERVAL),
            id='unfilled_orders',
            replace_existing=True
        )
        
        # 매일 자정에 데이터베이스 백업
        self.scheduler.add_job(
            self.db_manager.backup_database,
            CronTrigger(hour=0, minute=0),
            id='db_backup',
            replace_existing=True
        )
        
        # 매일 저녁 9시에 일일 보고서 생성
        self.scheduler.add_job(
            self.generate_daily_report,
            CronTrigger(hour=21, minute=0),
            id='daily_report',
            replace_existing=True
        )
    
    def execute_trade_cycle(self):
        """
        트레이딩 사이클 실행
        """
        with self.lock:
            if not self.running or not self.is_trading_hours():
                return
            
            self.logger.info("트레이딩 사이클 시작...")
            try:
                result = self.trading_logic.execute_trade_cycle()
                self.logger.info(f"트레이딩 사이클 완료: {result}")
            except Exception as e:
                self.logger.error(f"트레이딩 사이클 실행 중 오류 발생: {e}")
    
    def check_sell_signals(self):
        """
        매도 신호 확인
        """
        with self.lock:
            if not self.running:
                return
            
            self.logger.info("매도 신호 확인 중...")
            try:
                result = self.trading_logic.check_sell_signals()
                self.logger.info(f"매도 신호 확인 완료: {result}")
            except Exception as e:
                self.logger.error(f"매도 신호 확인 중 오류 발생: {e}")
    
    def handle_unfilled_orders(self):
        """
        미체결 주문 처리
        """
        with self.lock:
            if not self.running:
                return
            
            self.logger.info("미체결 주문 처리 중...")
            try:
                result = self.trading_logic.handle_unfilled_orders()
                if result['total'] > 0:
                    self.logger.info(f"미체결 주문 처리 완료: {result}")
            except Exception as e:
                self.logger.error(f"미체결 주문 처리 중 오류 발생: {e}")
    
    def generate_daily_report(self):
        """
        일일 보고서 생성
        """
        with self.lock:
            try:
                # 오늘 날짜
                today = datetime.now().strftime('%Y-%m-%d')
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                # 일일 거래 내역 조회
                orders = self.db_manager.get_orders_by_date_range(yesterday, today)
                
                # 일일 수익 계산
                profit = 0
                buy_count = 0
                sell_count = 0
                total_volume = 0
                
                for order in orders:
                    if order['type'] == 'BUY':
                        buy_count += 1
                    elif order['type'] == 'SELL':
                        sell_count += 1
                        # 수익 계산 로직 추가 필요
                
                # 잔고 조회
                accounts = self.trading_logic.get_account_balance()
                krw_balance = self.trading_logic.get_krw_balance()
                
                # 보고서 메시지 생성
                message = f"📊 일일 거래 보고서 ({yesterday})\n\n"
                message += f"▪️ 총 거래: {len(orders)}건 (매수: {buy_count}, 매도: {sell_count})\n"
                message += f"▪️ 예상 수익: {profit:,}원\n"
                message += f"▪️ KRW 잔고: {krw_balance:,}원\n"
                message += f"▪️ 보유 코인: {len(accounts) - 1}개"
                
                # 알림 전송
                self.notifier.send_notification(message, level="INFO", use_telegram=True)
                
                self.logger.info("일일 보고서 생성 완료")
                
            except Exception as e:
                self.logger.error(f"일일 보고서 생성 중 오류 발생: {e}")
    
    def start(self):
        """
        트레이딩 봇 시작
        """
        if self.running:
            self.logger.warning("트레이딩 봇이 이미 실행 중입니다.")
            return
        
        with self.lock:
            self.running = True
            
            # DB 초기화 확인
            self.db_manager.initialize_database()
            
            # 스케줄러 작업 등록
            self.schedule_jobs()
            
            # 스케줄러 시작
            self.scheduler.start()
            
            start_message = "🚀 암호화폐 트레이딩 봇 시작됨"
            self.logger.info(start_message)
            self.notifier.send_notification(start_message, use_slack=True, use_telegram=True)
    
    def stop(self):
        """
        트레이딩 봇 정지
        """
        if not self.running:
            return
        
        with self.lock:
            self.running = False
            
            # 스케줄러 종료
            if self.scheduler.running:
                self.scheduler.shutdown()
            
            stop_message = "🛑 암호화폐 트레이딩 봇 정지됨"
            self.logger.info(stop_message)
            self.notifier.send_notification(stop_message, use_slack=True, use_telegram=True)


if __name__ == "__main__":
    bot = TradingBot()
    
    try:
        bot.start()
        
        # 메인 스레드 유지
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        logging.error(f"예기치 않은 오류 발생: {e}")
        bot.stop()