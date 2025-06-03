"""
트레이딩 로직 모듈: 암호화폐 트레이딩 세션 관리와 주문 실행을 담당하는 클래스를 정의합니다.
"""

import threading
from datetime import datetime

from api.upbit_api import UpbitAPI
from database.db_manager import DatabaseManager
from trading.strategy.rsi_strategy import RSIStrategy
from utils.logger import Logger
from utils.notification import Notifier
from config.condition import (
    WAIT_TIME_BUY_CANCEL, WAIT_TIME_SELL_CANCEL, WAIT_TIME_ORDER_COMPLETE, MAX_RETRIES
)


class TradingLogic:
    """
    암호화폐 트레이딩 로직을 관리하는 클래스
    주문 실행, 상태 확인, 거래 내역 기록 등의 기능을 제공합니다.
    """
    
    def __init__(self, api=None, db_manager=None):
        """
        TradingLogic 클래스 초기화
        
        Args:
            api (UpbitAPI, optional): API 클래스 인스턴스
            db_manager (DatabaseManager, optional): 데이터베이스 관리자 인스턴스
        """
        self.api = api or UpbitAPI()
        self.db_manager = db_manager or DatabaseManager()
        self.logger = Logger()
        self.notifier = Notifier()
        
        # 기본 RSI 전략 생성
        self.strategy = RSIStrategy(self.api)
        
        # 트레이딩 락
        self.trading_lock = threading.Lock()
        
        # 활성 주문 목록 (메모리 캐시)
        self.active_orders = {}
    
    def get_ticker_list(self, market="KRW", limit=20):
        """
        거래 가능한 티커 목록 조회
        
        Args:
            market (str): 기준 시장 (KRW, BTC 등)
            limit (int): 조회할 티커 수
            
        Returns:
            list: 거래 가능한 티커 목록
        """
        try:
            all_markets = self.api.get_markets()
            tickers = [m['market'] for m in all_markets if m['market'].startswith(f"{market}-")]
            
            # 거래량 기준으로 상위 티커 선택
            ticker_info = []
            for ticker in tickers[:min(50, len(tickers))]:
                try:
                    ticker_data = self.api.get_ticker(ticker)[0]
                    ticker_info.append({
                        'ticker': ticker,
                        'volume': ticker_data.get('acc_trade_price_24h', 0)
                    })
                except Exception as e:
                    self.logger.error(f"{ticker} 정보 조회 중 오류: {e}")
                    continue
            
            # 거래량 기준 정렬
            ticker_info.sort(key=lambda x: x['volume'], reverse=True)
            
            return [t['ticker'] for t in ticker_info[:limit]]
            
        except Exception as e:
            self.logger.error(f"티커 목록 조회 중 오류 발생: {e}")
            return []
    
    def get_account_balance(self, ticker=None):
        """
        계좌 잔고 조회
        
        Args:
            ticker (str, optional): 특정 코인의 잔고를 조회할 경우 티커 지정
            
        Returns:
            dict: 잔고 정보
        """
        try:
            accounts = self.api.get_accounts()
            
            if ticker:
                currency = ticker.split('-')[1] if '-' in ticker else ticker
                for account in accounts:
                    if account['currency'] == currency:
                        return account
                return None
            
            return accounts
            
        except Exception as e:
            self.logger.error(f"잔고 조회 중 오류 발생: {e}")
            return None
    
    def get_krw_balance(self):
        """
        KRW 잔고 조회
        
        Returns:
            float: KRW 잔고
        """
        try:
            accounts = self.api.get_accounts()
            for account in accounts:
                if account['currency'] == 'KRW':
                    return float(account['balance'])
            return 0
        except Exception as e:
            self.logger.error(f"KRW 잔고 조회 중 오류 발생: {e}")
            return 0

    def buy_order(self, ticker, amount=None, price=None, portion=0.2):
        """
        매수 주문 실행
        
        Args:
            ticker (str): 코인 티커 (예: KRW-BTC)
            amount (float, optional): 매수할 금액 (KRW)
            price (float, optional): 지정가 주문 시 가격
            portion (float): 보유 KRW 중 사용할 비율 (0.0 ~ 1.0)
            
        Returns:
            dict: 주문 결과
        """
        with self.trading_lock:
            try:
                # 매수 금액이 지정되지 않은 경우 KRW 잔고의 portion 비율만큼 사용
                if amount is None:
                    krw_balance = self.get_krw_balance()
                    amount = krw_balance * portion
                    
                    # 최소 주문 금액 (5,000원) 확인
                    if amount < 5000:
                        self.logger.warning(f"최소 주문 금액(5,000원) 미만입니다: {amount}원")
                        return None
                
                # 현재가 조회
                if price is None:
                    ticker_info = self.api.get_ticker(ticker)[0]
                    price = float(ticker_info['trade_price'])
                
                # 주문 실행 (price는 매수 시 시장가로 주문)
                response = self.api.place_order(ticker, price=str(amount/price), side='bid', ord_type='price')
                
                if 'error' in response:
                    self.logger.error(f"{ticker} 매수 주문 실패: {response['error']['message']}")
                    return None
                
                # 주문 정보 저장
                order_id = response.get('uuid')
                if order_id:
                    order_info = {
                        'id': order_id,
                        'ticker': ticker,
                        'side': 'bid',
                        'price': price,
                        'amount': amount,
                        'status': 'wait',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # DB에 주문 정보 저장
                    self.db_manager.insert_order(
                        order_id, ticker, 'BUY', amount, price, 'WAIT',
                        strategy=self.strategy.name
                    )
                    
                    # 메모리에 활성 주문 추가
                    self.active_orders[order_id] = order_info
                    
                    # 알림 전송
                    self.notifier.notify_trade('BUY', ticker, price, amount, order_id)
                    
                    self.logger.info(f"{ticker} 매수 주문 성공: 주문량 {amount}원, 가격 {price}원, 주문ID {order_id}")
                    
                    return order_info
                else:
                    self.logger.error(f"{ticker} 매수 주문 실패: 주문ID를 받지 못함")
                    return None
                    
            except Exception as e:
                self.logger.error(f"{ticker} 매수 주문 중 오류 발생: {e}")
                return None
    
    def sell_order(self, ticker, volume=None, price=None, portion=1.0):
        """
        매도 주문 실행
        
        Args:
            ticker (str): 코인 티커 (예: KRW-BTC)
            volume (float, optional): 매도할 코인 수량
            price (float, optional): 지정가 주문 시 가격
            portion (float): 보유 코인 중 매도할 비율 (0.0 ~ 1.0)
            
        Returns:
            dict: 주문 결과
        """
        with self.trading_lock:
            try:
                # 코인 잔고 조회
                balance = self.get_account_balance(ticker)
                
                if not balance:
                    self.logger.warning(f"{ticker} 잔고가 없습니다.")
                    return None
                
                # 매도 수량이 지정되지 않은 경우 보유 수량의 portion 비율만큼 사용
                if volume is None:
                    volume = float(balance['balance']) * portion
                    
                    # 최소 주문 수량 확인
                    if volume <= 0:
                        self.logger.warning(f"{ticker} 매도 가능한 수량이 없습니다.")
                        return None
                
                # 현재가 조회
                if price is None:
                    ticker_info = self.api.get_ticker(ticker)[0]
                    price = float(ticker_info['trade_price'])
                
                # 주문 실행
                response = self.api.place_order(ticker, volume=volume, price=price, side='ask', ord_type='limit')
                
                if 'error' in response:
                    self.logger.error(f"{ticker} 매도 주문 실패: {response['error']['message']}")
                    return None
                
                # 주문 정보 저장
                order_id = response.get('uuid')
                if order_id:
                    order_info = {
                        'id': order_id,
                        'ticker': ticker,
                        'side': 'ask',
                        'price': price,
                        'volume': volume,
                        'status': 'wait',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # DB에 주문 정보 저장
                    self.db_manager.insert_order(
                        order_id, ticker, 'SELL', volume, price, 'WAIT',
                        strategy=self.strategy.name
                    )
                    
                    # 메모리에 활성 주문 추가
                    self.active_orders[order_id] = order_info
                    
                    # 알림 전송
                    self.notifier.notify_trade('SELL', ticker, price, volume, order_id)
                    
                    self.logger.info(f"{ticker} 매도 주문 성공: 주문량 {volume}, 가격 {price}원, 주문ID {order_id}")
                    
                    return order_info
                else:
                    self.logger.error(f"{ticker} 매도 주문 실패: 주문ID를 받지 못함")
                    return None
                    
            except Exception as e:
                self.logger.error(f"{ticker} 매도 주문 중 오류 발생: {e}")
                return None
    
    def check_order_status(self, order_id):
        """
        주문 상태 확인
        
        Args:
            order_id (str): 주문 ID
            
        Returns:
            dict: 주문 상태 정보
        """
        try:
            order_info = self.api.get_order_status(order_id)
            
            if 'error' in order_info:
                self.logger.error(f"주문 상태 조회 실패: {order_info['error']['message']}")
                return None
            
            # 주문 상태 업데이트
            if order_id in self.active_orders:
                self.active_orders[order_id]['status'] = order_info['state']
            
            # DB에 주문 정보 업데이트
            state = order_info['state']
            executed_volume = float(order_info.get('executed_volume', 0))
            executed_price = float(order_info.get('avg_price', 0))
            
            if state in ['done', 'cancel']:
                self.db_manager.update_order_status(order_id, state.upper(), executed_volume, executed_price)
                
                # 완료된 주문은 활성 주문 목록에서 제거
                if order_id in self.active_orders:
                    del self.active_orders[order_id]
            
            return order_info
            
        except Exception as e:
            self.logger.error(f"주문 상태 확인 중 오류 발생: {e}")
            return None
    
    def cancel_order(self, order_id):
        """
        주문 취소
        
        Args:
            order_id (str): 취소할 주문 ID
            
        Returns:
            bool: 취소 성공 여부
        """
        try:
            response = self.api.cancel_order(order_id)
            
            if 'error' in response:
                self.logger.error(f"주문 취소 실패: {response['error']['message']}")
                return False
            
            # DB에 주문 상태 업데이트
            self.db_manager.update_order_status(order_id, 'CANCEL')
            
            # 활성 주문 목록에서 제거
            if order_id in self.active_orders:
                del self.active_orders[order_id]
            
            self.logger.info(f"주문 취소 성공: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"주문 취소 중 오류 발생: {e}")
            return False
    
    def handle_unfilled_orders(self, max_wait_time=None):
        """
        미체결 주문 처리
        
        Args:
            max_wait_time (int, optional): 최대 대기 시간(초)
            
        Returns:
            dict: 처리 결과 통계
        """
        try:
            # 활성 주문 목록 복사
            active_orders = list(self.active_orders.items())
            result = {'total': len(active_orders), 'canceled': 0, 'done': 0, 'wait': 0}
            
            for order_id, order_info in active_orders:
                # 주문 상태 확인
                order_status = self.check_order_status(order_id)
                
                if not order_status:
                    continue
                
                state = order_status['state']
                side = order_status['side']
                
                # 주문 완료 상태
                if state == 'done':
                    result['done'] += 1
                    continue
                
                # 주문 취소 상태
                if state == 'cancel':
                    result['canceled'] += 1
                    continue
                
                # 미체결 주문 처리
                if state == 'wait':
                    # 주문 생성 시간 확인
                    created_at = datetime.strptime(order_info['created_at'], '%Y-%m-%d %H:%M:%S')
                    elapsed_time = (datetime.now() - created_at).total_seconds()
                    
                    # 대기 시간 설정
                    if max_wait_time is None:
                        max_wait_time = WAIT_TIME_BUY_CANCEL if side == 'bid' else WAIT_TIME_SELL_CANCEL
                    
                    # 최대 대기 시간 초과시 주문 취소
                    if elapsed_time > max_wait_time:
                        if self.cancel_order(order_id):
                            result['canceled'] += 1
                            self.logger.info(f"미체결 주문 자동 취소: {order_id}, 경과 시간: {elapsed_time:.0f}초")
                        else:
                            result['wait'] += 1
                    else:
                        result['wait'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"미체결 주문 처리 중 오류 발생: {e}")
            return {'total': 0, 'canceled': 0, 'done': 0, 'wait': 0, 'error': str(e)}
    
    def execute_trade_cycle(self, target_tickers=None, buy_amount=None, portion=0.2):
        """
        트레이딩 사이클 실행 (매수 신호 확인 및 매수 주문)
        
        Args:
            target_tickers (list, optional): 대상 티커 목록
            buy_amount (float, optional): 매수 금액
            portion (float): 보유 금액 대비 매수 비율
            
        Returns:
            dict: 실행 결과
        """
        try:
            # 대상 티커가 없으면 상위 거래량 코인 선택
            if not target_tickers:
                target_tickers = self.get_ticker_list(limit=20)
            
            result = {'total': len(target_tickers), 'buy_signals': 0, 'orders': 0}
            
            for ticker in target_tickers:
                # 매수 신호 확인
                if self.strategy.should_buy(ticker):
                    result['buy_signals'] += 1
                    
                    # 매수 주문 실행
                    order_result = self.buy_order(ticker, amount=buy_amount, portion=portion)
                    
                    if order_result:
                        result['orders'] += 1
            
            # 트레이딩 세션 기록
            self.db_manager.insert_trading_session('BUY', result['buy_signals'], result['orders'])
            
            return result
            
        except Exception as e:
            self.logger.error(f"트레이딩 사이클 실행 중 오류 발생: {e}")
            return {'error': str(e)}
    
    def check_sell_signals(self):
        """
        보유 중인 코인의 매도 신호 확인 및 매도 주문 실행
        
        Returns:
            dict: 실행 결과
        """
        try:
            # 보유 코인 목록 조회
            accounts = self.get_account_balance()
            result = {'total': 0, 'sell_signals': 0, 'orders': 0}
            
            for account in accounts:
                currency = account['currency']
                
                # KRW는 제외
                if currency == 'KRW':
                    continue
                
                balance = float(account['balance'])
                avg_buy_price = float(account.get('avg_buy_price', 0))
                
                # 잔고가 있는 경우만 처리
                if balance > 0 and avg_buy_price > 0:
                    result['total'] += 1
                    
                    # 티커 포맷 변환
                    ticker = f"KRW-{currency}"
                    
                    # 매도 신호 확인
                    current_price = self.api.get_ticker(ticker)[0]['trade_price']
                    
                    if self.strategy.should_sell(ticker, avg_buy_price, current_price):
                        result['sell_signals'] += 1
                        
                        # 매도 주문 실행
                        order_result = self.sell_order(ticker, volume=balance)
                        
                        if order_result:
                            result['orders'] += 1
            
            # 트레이딩 세션 기록
            if result['total'] > 0:
                self.db_manager.insert_trading_session('SELL', result['sell_signals'], result['orders'])
            
            return result
            
        except Exception as e:
            self.logger.error(f"매도 신호 확인 중 오류 발생: {e}")
            return {'error': str(e)}