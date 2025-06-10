"""
업비트 API 클라이언트

업비트 REST API와 상호작용하는 클래스를 제공합니다.
JWT 인증을 사용하여 API 호출을 수행합니다.
"""
import requests
import jwt
import uuid
import hashlib
import logging
import time
from urllib.parse import urlencode
from datetime import datetime, timedelta
from requests.exceptions import RequestException
from config.config import (
    UPBIT_ACCESS_KEY, UPBIT_API_URL,
    API_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)
from database.db_manager import DatabaseManager


class UpbitApi:
    """업비트 API와 상호작용하기 위한 클래스"""
    
    def __init__(self):
        """UpbitApi 클래스 인스턴스를 초기화합니다."""
        self.base_url = UPBIT_API_URL
        self.access_key = UPBIT_ACCESS_KEY
        self.db_manager = DatabaseManager()
        self.token = None
        self.token_expires_at = None
        
    def _get_jwt_token(self, params=None):
        """
        지정된 파라미터로 JWT 토큰을 생성합니다.
        
        Args:
            params (dict, optional): 쿼리 파라미터
            
        Returns:
            str: 생성된 JWT 토큰
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        # 파라미터가 있는 경우 query_hash 생성
        if params:
            query_string = urlencode(params)
            hash_value = hashlib.sha512(query_string.encode()).hexdigest()
            payload['query_hash'] = hash_value
            payload['query_hash_alg'] = 'SHA512'
            
        return jwt.encode(payload, self.access_key)
    
    def _get_headers(self, params=None):
        """
        API 요청에 필요한 헤더를 설정합니다.
        
        Args:
            params (dict, optional): 쿼리 파라미터
            
        Returns:
            dict: 요청 헤더
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        token = self._get_jwt_token(params)
        headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    def _request(self, method, endpoint, params=None, data=None, retry=0):
        """
        API 요청을 수행합니다.
        
        Args:
            method (str): HTTP 메서드 ('GET', 'POST', 'DELETE' 등)
            endpoint (str): API 엔드포인트
            params (dict, optional): 쿼리 파라미터
            data (dict, optional): 요청 데이터
            retry (int): 재시도 횟수
            
        Returns:
            dict: API 응답 데이터 또는 실패 시 None
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(params)
        
        try:
            response = requests.request(
                method, 
                url, 
                headers=headers, 
                params=params, 
                json=data, 
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logging.error(f"API 요청 오류: {e}")
            if retry < MAX_RETRIES:
                logging.info(f"{retry+1}회 재시도 중...")
                time.sleep(RETRY_DELAY)
                return self._request(method, endpoint, params, data, retry+1)
            return None
    
    #####################################################
    ##########         계좌 조회 관련         ############
    #####################################################
    
    def get_accounts(self):
        """
        전체 계좌 조회
        
        Returns:
            list: 보유 계좌 리스트 또는 실패 시 None
        """
        return self._request('GET', '/v1/accounts')
    
    def get_order_chance(self, market):
        """
        주문 가능 정보 조회
        
        Args:
            market (str): 마켓 ID (예: KRW-BTC)
            
        Returns:
            dict: 주문 가능 정보 또는 실패 시 None
        """
        params = {'market': market}
        return self._request('GET', '/v1/orders/chance', params=params)
    
    #####################################################
    ##########         주문 관련              ############
    #####################################################
    
    def place_order(self, market, side, volume=None, price=None, ord_type=None):
        """
        주문하기
        
        Args:
            market (str): 마켓 ID (예: KRW-BTC)
            side (str): 주문 종류 (bid: 매수, ask: 매도)
            volume (str, optional): 주문량
            price (str, optional): 주문 가격
            ord_type (str, optional): 주문 타입 (limit: 지정가, price: 시장가 매수, market: 시장가 매도)
            
        Returns:
            dict: 주문 정보 또는 실패 시 None
        """
        data = {'market': market, 'side': side}
        
        if volume is not None:
            data['volume'] = str(volume)
        
        if price is not None:
            data['price'] = str(price)
            
        if ord_type is not None:
            data['ord_type'] = ord_type
            
        return self._request('POST', '/v1/orders', data=data)
    
    def cancel_order(self, uuid=None, identifier=None):
        """
        주문 취소
        
        Args:
            uuid (str, optional): 취소할 주문의 UUID
            identifier (str, optional): 조회용 사용자 지정 값
            
        Returns:
            dict: 취소된 주문 정보 또는 실패 시 None
        """
        data = {}
        if uuid is not None:
            data['uuid'] = uuid
        if identifier is not None:
            data['identifier'] = identifier
            
        return self._request('DELETE', '/v1/order', data=data)
    
    def get_order(self, uuid=None, identifier=None):
        """
        개별 주문 조회
        
        Args:
            uuid (str, optional): 조회할 주문의 UUID
            identifier (str, optional): 조회용 사용자 지정 값
            
        Returns:
            dict: 주문 정보 또는 실패 시 None
        """
        params = {}
        if uuid is not None:
            params['uuid'] = uuid
        if identifier is not None:
            params['identifier'] = identifier
            
        return self._request('GET', '/v1/order', params=params)
    
    def get_orders(self, market=None, state=None, page=1, limit=100):
        """
        주문 리스트 조회
        
        Args:
            market (str, optional): 마켓 ID
            state (str, optional): 주문 상태
            page (int, optional): 페이지 번호
            limit (int, optional): 페이지 당 결과 수
            
        Returns:
            list: 주문 목록 또는 실패 시 None
        """
        params = {'page': page, 'limit': limit}
        if market is not None:
            params['market'] = market
        if state is not None:
            params['state'] = state
            
        return self._request('GET', '/v1/orders', params=params)
    
    #####################################################
    ##########        시세 정보 조회         ############
    #####################################################
    
    def get_ticker(self, markets):
        """
        현재가 정보 조회
        
        Args:
            markets (str): 마켓 코드 목록 (쉼표로 구분, 최대 100개)
            
        Returns:
            list: 현재가 정보 또는 실패 시 None
        """
        params = {'markets': markets}
        return self._request('GET', '/v1/ticker', params=params)
    
    def get_orderbook(self, markets):
        """
        호가 정보 조회
        
        Args:
            markets (str): 마켓 코드 목록 (쉼표로 구분, 최대 100개)
            
        Returns:
            list: 호가 정보 또는 실패 시 None
        """
        params = {'markets': markets}
        return self._request('GET', '/v1/orderbook', params=params)
    
    def get_market_all(self, is_details=False):
        """
        마켓 코드 조회
        
        Args:
            is_details (bool, optional): 상세 정보 포함 여부
            
        Returns:
            list: 마켓 코드 목록 또는 실패 시 None
        """
        params = {'isDetails': 'true' if is_details else 'false'}
        return self._request('GET', '/v1/market/all', params=params)
    
    #####################################################
    ##########          캔들 조회           ############
    #####################################################
    
    def get_candles_minutes(self, unit, market, count=1, to=None):
        """
        분(minute) 캔들 조회
        
        Args:
            unit (int): 분 단위 (1, 3, 5, 15, 10, 30, 60, 240)
            market (str): 마켓 코드 (예: KRW-BTC)
            count (int, optional): 캔들 개수 (최대 200)
            to (str, optional): 마지막 캔들 시간 (포맷: yyyy-MM-dd'T'HH:mm:ss)
            
        Returns:
            list: 캔들 정보 또는 실패 시 None
        """
        params = {'market': market, 'count': count}
        if to is not None:
            params['to'] = to
            
        return self._request('GET', f'/v1/candles/minutes/{unit}', params=params)
    
    def get_candles_days(self, market, count=1, to=None):
        """
        일(Day) 캔들 조회
        
        Args:
            market (str): 마켓 코드 (예: KRW-BTC)
            count (int, optional): 캔들 개수 (최대 200)
            to (str, optional): 마지막 캔들 시간 (포맷: yyyy-MM-dd'T'HH:mm:ss)
            
        Returns:
            list: 캔들 정보 또는 실패 시 None
        """
        params = {'market': market, 'count': count}
        if to is not None:
            params['to'] = to
            
        return self._request('GET', '/v1/candles/days', params=params)
    
    def get_candles_weeks(self, market, count=1, to=None):
        """
        주(Week) 캔들 조회
        
        Args:
            market (str): 마켓 코드 (예: KRW-BTC)
            count (int, optional): 캔들 개수 (최대 200)
            to (str, optional): 마지막 캔들 시간 (포맷: yyyy-MM-dd'T'HH:mm:ss)
            
        Returns:
            list: 캔들 정보 또는 실패 시 None
        """
        params = {'market': market, 'count': count}
        if to is not None:
            params['to'] = to
            
        return self._request('GET', '/v1/candles/weeks', params=params)
    
    def get_candles_months(self, market, count=1, to=None):
        """
        월(Month) 캔들 조회
        
        Args:
            market (str): 마켓 코드 (예: KRW-BTC)
            count (int, optional): 캔들 개수 (최대 200)
            to (str, optional): 마지막 캔들 시간 (포맷: yyyy-MM-dd'T'HH:mm:ss)
            
        Returns:
            list: 캔들 정보 또는 실패 시 None
        """
        params = {'market': market, 'count': count}
        if to is not None:
            params['to'] = to
            
        return self._request('GET', '/v1/candles/months', params=params)
    
    #####################################################
    ##########        입출금 관련 API         ############
    #####################################################
    
    def get_deposits_status(self, currency=None, txid=None, limit=100):
        """
        입금 내역 조회
        
        Args:
            currency (str, optional): 화폐 코드
            txid (str, optional): 트랜잭션 ID
            limit (int, optional): 조회 개수 (최대 100)
            
        Returns:
            list: 입금 내역 또는 실패 시 None
        """
        params = {'limit': limit}
        if currency is not None:
            params['currency'] = currency
        if txid is not None:
            params['txid'] = txid
            
        return self._request('GET', '/v1/deposits', params=params)
    
    def get_withdraws_status(self, currency=None, txid=None, limit=100):
        """
        출금 내역 조회
        
        Args:
            currency (str, optional): 화폐 코드
            txid (str, optional): 트랜잭션 ID
            limit (int, optional): 조회 개수 (최대 100)
            
        Returns:
            list: 출금 내역 또는 실패 시 None
        """
        params = {'limit': limit}
        if currency is not None:
            params['currency'] = currency
        if txid is not None:
            params['txid'] = txid
            
        return self._request('GET', '/v1/withdraws', params=params)
    
    def get_deposit_addresses(self):
        """
        입금 주소 조회
        
        Returns:
            list: 입금 주소 목록 또는 실패 시 None
        """
        return self._request('GET', '/v1/deposits/addresses')
    
    def get_withdraw_addresses(self):
        """
        출금 주소 조회
        
        Returns:
            list: 출금 주소 목록 또는 실패 시 None
        """
        return self._request('GET', '/v1/withdraws/addresses')