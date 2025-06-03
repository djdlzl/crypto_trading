"""
업비트 REST API 모듈: 업비트 거래소 API와 통신하는 클래스를 정의합니다.
"""

import uuid
import jwt
import hashlib
import requests
import time
from urllib.parse import urlencode
from config.config import *
from utils.logger import Logger


class UpbitAPI:
    """업비트 API와 통신하는 클래스"""
    
    def __init__(self):
        """UpbitAPI 클래스 초기화"""
        self.base_url = "https://api.upbit.com"
        self.access_key = UPBIT_ACCESS_KEY
        self.secret_key = UPBIT_SECRET_KEY
        self.logger = Logger()
        
    def _get_auth_header(self, query=None):
        """
        인증 헤더 생성
        
        Args:
            query (dict, optional): 쿼리 파라미터
            
        Returns:
            dict: 인증 헤더
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4())
        }
        
        if query:
            m = hashlib.sha512()
            m.update(urlencode(query).encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
            
        jwt_token = jwt.encode(payload, self.secret_key)
        
        # PyJWT 버전에 따라 반환 형식이 다를 수 있음
        if isinstance(jwt_token, bytes):
            jwt_token = jwt_token.decode('utf-8')
            
        return {"Authorization": f"Bearer {jwt_token}"}
    
    def _request(self, method, url_path, params=None, data=None, retries=3, delay=1):
        """
        API 요청 함수
        
        Args:
            method (str): 요청 메소드 ('GET', 'POST', 'DELETE')
            url_path (str): API 엔드포인트 경로
            params (dict, optional): URL 쿼리 파라미터
            data (dict, optional): 요청 바디 데이터
            retries (int): 재시도 횟수
            delay (int): 재시도 간 대기 시간(초)
            
        Returns:
            dict: API 응답 데이터
        """
        url = f"{self.base_url}{url_path}"
        headers = self._get_auth_header(params if method == 'GET' else data)
        
        for attempt in range(retries):
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, json=data, headers=headers, timeout=10)
                elif method == 'DELETE':
                    response = requests.delete(url, json=data, headers=headers, timeout=10)
                else:
                    raise ValueError(f"지원하지 않는 메소드입니다: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API 요청 오류 (시도 {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise
    
    def get_ticker(self, ticker):
        """
        현재가 정보 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC') 또는 여러 티커를 콤마로 구분한 문자열
            
        Returns:
            list: 현재가 정보 리스트
        """
        params = {'markets': ticker}
        return self._request('GET', '/v1/ticker', params=params)
    
    def get_minutes_candles(self, ticker, unit=1, count=200):
        """
        분(minute) 캔들 데이터 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            unit (int): 분 단위 (1, 3, 5, 15, 10, 30, 60, 240 중 하나)
            count (int): 데이터 개수 (최대 200)
            
        Returns:
            list: 캔들 데이터 목록
        """
        url = f'/v1/candles/minutes/{unit}'
        params = {
            'market': ticker,
            'count': count
        }
        return self._request('GET', url, params=params)
    
    def get_days_candles(self, ticker, count=200):
        """
        일(day) 캔들 데이터 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            count (int): 데이터 개수 (최대 200)
            
        Returns:
            list: 캔들 데이터 목록
        """
        params = {
            'market': ticker,
            'count': count
        }
        return self._request('GET', '/v1/candles/days', params=params)
    
    def get_weeks_candles(self, ticker, count=200):
        """
        주(week) 캔들 데이터 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            count (int): 데이터 개수 (최대 200)
            
        Returns:
            list: 캔들 데이터 목록
        """
        params = {
            'market': ticker,
            'count': count
        }
        return self._request('GET', '/v1/candles/weeks', params=params)
    
    def get_months_candles(self, ticker, count=200):
        """
        월(month) 캔들 데이터 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            count (int): 데이터 개수 (최대 200)
            
        Returns:
            list: 캔들 데이터 목록
        """
        params = {
            'market': ticker,
            'count': count
        }
        return self._request('GET', '/v1/candles/months', params=params)
    
    def get_order_book(self, ticker):
        """
        호가 정보 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            
        Returns:
            dict: 호가 정보
        """
        params = {'markets': ticker}
        return self._request('GET', '/v1/orderbook', params=params)
    
    def get_market_all(self):
        """
        마켓 코드 조회
        
        Returns:
            list: 마켓 코드 목록
        """
        return self._request('GET', '/v1/market/all')
    
    def place_order(self, ticker, volume=None, price=None, side='bid', ord_type='limit'):
        """
        주문 실행 (매수/매도)
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            volume (float, optional): 주문 수량 (시장가 매수일 때는 None)
            price (float, optional): 주문 가격 (시장가 매도일 때는 None)
            side (str): 주문 종류 ('bid': 매수, 'ask': 매도)
            ord_type (str): 주문 타입 ('limit': 지정가, 'price': 시장가 매수, 'market': 시장가 매도)
            
        Returns:
            dict: 주문 결과
        """
        data = {
            'market': ticker,
            'side': side,
            'ord_type': ord_type
        }
        
        if volume is not None:
            data['volume'] = str(volume)
        if price is not None:
            data['price'] = str(price)
            
        return self._request('POST', '/v1/orders', data=data)
    
    def cancel_order(self, order_id):
        """
        주문 취소
        
        Args:
            order_id (str): 주문 UUID
            
        Returns:
            dict: 취소 결과
        """
        data = {'uuid': order_id}
        return self._request('DELETE', '/v1/order', data=data)
    
    def get_order_status(self, order_id):
        """
        주문 상태 확인
        
        Args:
            order_id (str): 주문 UUID
            
        Returns:
            dict: 주문 상태 정보
        """
        params = {'uuid': order_id}
        return self._request('GET', '/v1/order', params=params)
    
    def get_orders(self, ticker, state='wait', page=1):
        """
        주문 목록 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            state (str): 주문 상태 ('wait': 체결 대기, 'watch': 예약 주문, 'done': 전체 체결, 'cancel': 주문 취소)
            page (int): 페이지 번호
            
        Returns:
            list: 주문 목록
        """
        params = {
            'market': ticker,
            'state': state,
            'page': page
        }
        return self._request('GET', '/v1/orders', params=params)
    
    def get_accounts(self):
        """
        보유 자산 조회
        
        Returns:
            list: 보유 자산 목록
        """
        return self._request('GET', '/v1/accounts')
    
    def get_balance(self, ticker=None):
        """
        특정 코인 잔액 조회
        
        Args:
            ticker (str, optional): 코인 티커 (예: 'KRW-BTC' -> 'BTC'로 변환해서 사용)
            
        Returns:
            float: 잔액 또는 전체 잔액 정보
        """
        accounts = self.get_accounts()
        
        if ticker:
            # KRW-BTC 형태에서 BTC만 추출
            if '-' in ticker:
                ticker = ticker.split('-')[1]
                
            for account in accounts:
                if account['currency'] == ticker:
                    return float(account['balance'])
            return 0.0
        
        # 전체 잔액 정보 반환
        return accounts
        
    def get_deposits(self, currency=None, state=None, limit=100):
        """
        입금 내역 조회
        
        Args:
            currency (str, optional): 통화 코드 (예: 'BTC')
            state (str, optional): 입금 상태 ('submitting', 'submitted', 'almost_accepted', 'rejected', 'accepted', 'processing')
            limit (int, optional): 조회 개수 (최대 100)
            
        Returns:
            list: 입금 내역 목록
        """
        params = {'limit': limit}
        if currency:
            params['currency'] = currency
        if state:
            params['state'] = state
            
        return self._request('GET', '/v1/deposits', params=params)
    
    def get_withdraws(self, currency=None, state=None, limit=100):
        """
        출금 내역 조회
        
        Args:
            currency (str, optional): 통화 코드 (예: 'BTC')
            state (str, optional): 출금 상태 ('submitting', 'submitted', 'almost_accepted', 'rejected', 'accepted', 'processing')
            limit (int, optional): 조회 개수 (최대 100)
            
        Returns:
            list: 출금 내역 목록
        """
        params = {'limit': limit}
        if currency:
            params['currency'] = currency
        if state:
            params['state'] = state
            
        return self._request('GET', '/v1/withdraws', params=params)
    
    def withdraw_coin(self, currency, amount, address, secondary_address=None):
        """
        디지털 자산 출금하기
        
        Args:
            currency (str): 통화 코드 (예: 'BTC')
            amount (str): 출금 수량
            address (str): 출금 주소
            secondary_address (str, optional): 2차 출금 주소 (일부 코인만 해당)
            
        Returns:
            dict: 출금 요청 결과
        """
        data = {
            'currency': currency,
            'amount': str(amount),
            'address': address
        }
        
        if secondary_address:
            data['secondary_address'] = secondary_address
            
        return self._request('POST', '/v1/withdraws/coin', data=data)
    
    def withdraw_krw(self, amount):
        """
        원화 출금하기
        
        Args:
            amount (str): 출금 금액
            
        Returns:
            dict: 출금 요청 결과
        """
        data = {'amount': str(amount)}
        return self._request('POST', '/v1/withdraws/krw', data=data)
    
    def get_order_chance(self, ticker):
        """
        주문 가능 정보 조회
        
        Args:
            ticker (str): 코인 티커 (예: 'KRW-BTC')
            
        Returns:
            dict: 주문 가능 정보
        """
        params = {'market': ticker}
        return self._request('GET', '/v1/orders/chance', params=params)
    
    def get_deposit_addresses(self):
        """
        전체 입금 주소 조회
        
        Returns:
            list: 입금 주소 목록
        """
        return self._request('GET', '/v1/deposits/coin_addresses')
    
    def get_deposit_address(self, currency):
        """
        개별 입금 주소 조회
        
        Args:
            currency (str): 통화 코드 (예: 'BTC')
            
        Returns:
            dict: 입금 주소 정보
        """
        params = {'currency': currency}
        return self._request('GET', '/v1/deposits/coin_address', params=params)
    
    def create_deposit_address(self, currency):
        """
        입금 주소 생성 요청
        
        Args:
            currency (str): 통화 코드 (예: 'BTC')
            
        Returns:
            dict: 입금 주소 생성 결과
        """
        data = {'currency': currency}
        return self._request('POST', '/v1/deposits/generate_coin_address', data=data)
