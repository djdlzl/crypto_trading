"""
업비트 웹소켓 모듈

업비트 웹소켓 API를 사용하여 실시간 시세 및 체결 정보를 수신합니다.
"""
import json
import uuid
import logging
import asyncio
import websockets
import jwt
from datetime import datetime, timedelta
from websockets.exceptions import ConnectionClosed
from config.config import (
    UPBIT_ACCESS_KEY,  UPBIT_WS_URL,
    TOKEN_REFRESH_INTERVAL, MAX_RETRIES, RETRY_DELAY
)
from database.db_manager import DatabaseManager


class UpbitWebSocket:
    """업비트 웹소켓 API와 상호작용하기 위한 클래스"""
    
    def __init__(self, callback=None):
        """
        UpbitWebSocket 클래스의 인스턴스를 초기화합니다.
        
        Args:
            callback (callable, optional): 메시지 수신 시 호출할 콜백 함수
        """
        self.url = UPBIT_WS_URL
        self.access_key = UPBIT_ACCESS_KEY
        self.db_manager = DatabaseManager()
        self.websocket = None
        self.is_connected = False
        self.callback = callback
        self.subscribed_markets = set()
        self.subscribed_types = {}  # {market: [type1, type2, ...]}
        self.auth_token = None
        self.auth_expires_at = None
        self.message_queue = asyncio.Queue()
        self.active_tasks = {}
        self.locks = {}  # 시장별 락 관리
        self.LOCK_TIMEOUT = 10
        self._loop = None
        
    ######################################################################################
    #########################    인증 관련 메서드   #######################################
    ######################################################################################
    
    def _create_jwt_token(self):
        """
        웹소켓 인증을 위한 JWT 토큰을 생성합니다.
        
        Returns:
            str: 생성된 JWT 토큰
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        return jwt.encode(payload, self.secret_key)
    
    async def _ensure_auth(self):
        """
        유효한 웹소켓 인증 토큰이 있는지 확인하고, 필요한 경우 새 토큰을 생성합니다.
        
        Returns:
            str: 유효한 인증 토큰
        """
        now = datetime.now()
        
        # 캐시된 토큰이 있고 유효한지 확인
        if self.auth_token and self.auth_expires_at and now < self.auth_expires_at:
            return self.auth_token
        
        # DB에 저장된 토큰이 있는지 확인
        cached_token, cached_expires_at = self.db_manager.get_auth('websocket')
        if cached_token and cached_expires_at > datetime.now():
            self.auth_token = cached_token
            self.auth_expires_at = cached_expires_at
            return self.auth_token
        
        # 새 토큰 생성
        self.auth_token = self._create_jwt_token()
        self.auth_expires_at = datetime.now() + timedelta(seconds=TOKEN_REFRESH_INTERVAL)
        
        # DB에 저장
        self.db_manager.save_auth('websocket', self.auth_token, self.auth_expires_at)
        
        return self.auth_token
    
    ######################################################################################
    #########################    웹소켓 연결 메서드   #####################################
    ######################################################################################
    
    async def connect(self):
        """웹소켓 연결을 설정합니다."""
        if self.websocket and not self.websocket.closed:
            logging.info("웹소켓이 이미 연결되어 있습니다.")
            return
        
        try:
            # 기존 웹소켓 정리
            if self.websocket:
                try:
                    await self.websocket.close()
                except Exception as e:
                    logging.error(f"웹소켓 종료 오류: {e}")
                self.websocket = None
            
            # 새 웹소켓 연결
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            self._loop = asyncio.get_running_loop()
            logging.info("웹소켓 연결 성공")
            
            # 기존 구독 복원
            if self.subscribed_markets:
                await self.resubscribe_all()
            
        except Exception as e:
            self.is_connected = False
            self.websocket = None
            logging.error(f"웹소켓 연결 오류: {e}")
            raise
    
    async def close(self):
        """웹소켓 연결을 종료합니다."""
        if self.websocket:
            try:
                await self.websocket.close()
                logging.info("웹소켓 연결 종료")
            except Exception as e:
                logging.error(f"웹소켓 종료 오류: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
    
    ######################################################################################
    #########################    구독 관련 메서드   #######################################
    ######################################################################################
    
    async def subscribe_ticker(self, markets):
        """
        현재가(ticker) 정보를 구독합니다.
        
        Args:
            markets (list): 마켓 코드 목록 (예: ['KRW-BTC', 'KRW-ETH'])
            
        Returns:
            bool: 성공 여부
        """
        return await self._subscribe('ticker', markets)
    
    async def subscribe_orderbook(self, markets):
        """
        호가(orderbook) 정보를 구독합니다.
        
        Args:
            markets (list): 마켓 코드 목록 (예: ['KRW-BTC', 'KRW-ETH'])
            
        Returns:
            bool: 성공 여부
        """
        return await self._subscribe('orderbook', markets)
    
    async def subscribe_trade(self, markets):
        """
        체결(trade) 정보를 구독합니다.
        
        Args:
            markets (list): 마켓 코드 목록 (예: ['KRW-BTC', 'KRW-ETH'])
            
        Returns:
            bool: 성공 여부
        """
        return await self._subscribe('trade', markets)
    
    async def _subscribe(self, type_name, markets):
        """
        지정된 타입과 마켓에 대한 데이터를 구독합니다.
        
        Args:
            type_name (str): 구독 타입 ('ticker', 'orderbook', 'trade')
            markets (list): 마켓 코드 목록
            
        Returns:
            bool: 성공 여부
        """
        if not self.is_connected or not self.websocket:
            await self.connect()
        
        try:
            # 구독 요청 메시지 생성
            message = [
                {'ticket': str(uuid.uuid4())},
                {
                    'type': type_name, 
                    'codes': markets,
                    'isOnlyRealtime': True
                }
            ]
            
            # 개인 정보 구독이 필요한 경우 인증 추가
            if type_name in ['ticker', 'orderbook', 'trade']:
                auth_token = await self._ensure_auth()
                message.append({'format': 'SIMPLE'})
            
            # 구독 요청 전송
            await self.websocket.send(json.dumps(message))
            
            # 구독 정보 업데이트
            for market in markets:
                self.subscribed_markets.add(market)
                if market not in self.subscribed_types:
                    self.subscribed_types[market] = []
                if type_name not in self.subscribed_types[market]:
                    self.subscribed_types[market].append(type_name)
            
            logging.info(f"{type_name} 타입 구독 성공: {markets}")
            return True
            
        except Exception as e:
            logging.error(f"구독 오류 ({type_name}): {e}")
            self.is_connected = False
            self.websocket = None
            return False
    
    async def unsubscribe(self, market, type_name=None):
        """
        특정 마켓의 구독을 취소합니다.
        
        Args:
            market (str): 마켓 코드 (예: 'KRW-BTC')
            type_name (str, optional): 구독 타입. None이면 모든 타입의 구독 취소.
            
        Returns:
            bool: 성공 여부
        """
        if market not in self.subscribed_markets:
            logging.warning(f"구독되지 않은 마켓: {market}")
            return False
        
        if type_name and market in self.subscribed_types:
            if type_name in self.subscribed_types[market]:
                self.subscribed_types[market].remove(type_name)
                if not self.subscribed_types[market]:
                    del self.subscribed_types[market]
                    self.subscribed_markets.remove(market)
        else:
            # 모든 타입 구독 취소
            if market in self.subscribed_types:
                del self.subscribed_types[market]
            self.subscribed_markets.remove(market)
        
        # 웹소켓 재연결하여 구독 갱신
        try:
            await self.close()
            await self.connect()
            await self.resubscribe_all()
            logging.info(f"{market} 구독 취소 성공")
            return True
        except Exception as e:
            logging.error(f"구독 취소 오류: {e}")
            return False
    
    async def resubscribe_all(self):
        """모든 활성 구독을 다시 설정합니다."""
        if not self.subscribed_types:
            return
        
        # 타입별로 구독 요청
        for type_name in ['ticker', 'orderbook', 'trade']:
            markets = []
            for market, types in self.subscribed_types.items():
                if type_name in types:
                    markets.append(market)
            
            if markets:
                await self._subscribe(type_name, markets)
    
    ######################################################################################
    #########################    메시지 처리 메서드   #####################################
    ######################################################################################
    
    async def start_monitoring(self):
        """실시간 모니터링을 시작합니다."""
        try:
            # 웹소켓 연결
            if not self.is_connected:
                await self.connect()
            
            # 메시지 수신 태스크 시작
            receiver_task = asyncio.create_task(self._message_receiver())
            
            # 메시지 처리 태스크 시작
            processor_task = asyncio.create_task(self._message_processor())
            
            # 태스크 완료 대기
            await asyncio.gather(receiver_task, processor_task)
            
        except Exception as e:
            logging.error(f"모니터링 중 오류 발생: {e}")
            await self.close()
    
    async def _message_receiver(self):
        """웹소켓 메시지를 수신하는 코루틴"""
        while True:
            try:
                # 웹소켓 연결 상태 확인
                if not self.is_connected or not self.websocket:
                    try:
                        logging.info("웹소켓 재연결 시도...")
                        await self.connect()
                        if not self.is_connected or not self.websocket:
                            logging.warning("웹소켓 재연결 실패, 5초 후 재시도")
                            await asyncio.sleep(5)
                            continue
                    except Exception as e:
                        logging.error(f"재연결 실패: {e}")
                        await asyncio.sleep(5)
                        continue
                
                # 웹소켓이 닫혔는지 추가 확인
                if self.websocket.closed:
                    logging.warning("웹소켓이 닫혀있음, 재연결 필요")
                    self.is_connected = False
                    self.websocket = None
                    continue
                
                # 웹소켓 응답 수신
                data = await self.websocket.recv()
                
                # 핑/퐁 메시지 처리
                if "ping" in data:
                    await self.websocket.send(json.dumps({"pong": True}))
                    continue
                
                # 데이터 파싱
                try:
                    message = json.loads(data)
                    await self.message_queue.put(message)
                except json.JSONDecodeError:
                    logging.error(f"JSON 파싱 오류: {data}")
                
            except ConnectionClosed:
                logging.warning("웹소켓 연결이 끊어졌습니다. 재연결을 시도합니다.")
                self.is_connected = False
                self.websocket = None
                await asyncio.sleep(1)
                continue
            
            except Exception as e:
                logging.error(f"메시지 수신 중 오류: {e}")
                self.is_connected = False
                self.websocket = None
                await asyncio.sleep(1)
                continue
    
    async def _message_processor(self):
        """수신된 메시지를 처리하는 코루틴"""
        while True:
            try:
                # 큐에서 메시지 가져오기
                message = await self.message_queue.get()
                
                # 콜백 함수가 있으면 호출
                if self.callback:
                    try:
                        await self.callback(message)
                    except Exception as e:
                        logging.error(f"콜백 처리 오류: {e}")
                
                self.message_queue.task_done()
                
            except Exception as e:
                logging.error(f"메시지 처리 중 오류: {e}")
                await asyncio.sleep(1)