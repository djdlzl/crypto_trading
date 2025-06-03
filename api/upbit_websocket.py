"""
업비트 웹소켓 API 모듈: 실시간 시세 데이터를 구독하는 클래스를 정의합니다.
"""

import json
import asyncio
import websockets
import uuid
import jwt
from datetime import datetime

from config.config import UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY
from utils.logger import Logger


class UpbitWebSocket:
    """업비트 웹소켓 API 클래스"""
    
    def __init__(self, tickers, callback=None):
        """
        UpbitWebSocket 클래스 초기화
        
        Args:
            tickers (list): 구독할 코인 티커 목록 (예: ['KRW-BTC', 'KRW-ETH'])
            callback (callable, optional): 메시지 수신 시 호출할 콜백 함수
        """
        self.ws_url = "wss://api.upbit.com/websocket/v1"
        self.tickers = tickers if isinstance(tickers, list) else [tickers]
        self.callback = callback
        self.websocket = None
        self.logger = Logger()
        self.running = False
        
    async def connect(self):
        """
        웹소켓 연결 및 데이터 수신 루프 시작
        """
        try:
            self.running = True
            self.logger.info(f"웹소켓 연결 시도: {', '.join(self.tickers)}")
            
            # 구독 형식 설정
            subscribe_fmt = [
                {"ticket": str(uuid.uuid4())},
                {
                    "type": "ticker",
                    "codes": self.tickers,
                    "isOnlyRealtime": True
                }
            ]
            
            # 웹소켓 연결
            async with websockets.connect(self.ws_url) as websocket:
                self.websocket = websocket
                self.logger.info("웹소켓 연결 성공")
                
                # 구독 요청 전송
                await websocket.send(json.dumps(subscribe_fmt))
                
                # 메시지 수신 루프
                while self.running:
                    try:
                        message = await websocket.recv()
                        await self._handle_message(message)
                    except websockets.exceptions.ConnectionClosed:
                        self.logger.error("웹소켓 연결이 종료되었습니다. 재연결 시도 중...")
                        break
        
        except Exception as e:
            self.logger.error(f"웹소켓 오류 발생: {e}")
        
        finally:
            self.running = False
            # 연결이 끊어진 경우 3초 후 재연결 시도
            if self.running:
                self.logger.info("웹소켓 재연결 시도 중...")
                await asyncio.sleep(3)
                await self.connect()
    
    async def _handle_message(self, message):
        """
        수신된 메시지 처리
        
        Args:
            message (str): 수신된 웹소켓 메시지
        """
        try:
            # 바이너리 메시지를 JSON으로 변환
            data = json.loads(message)
            
            # 로그 기록 (너무 많은 메시지로 로그가 가득차지 않도록 필요시에만 활성화)
            # self.logger.debug(f"웹소켓 메시지 수신: {data.get('code')} - {data.get('trade_price')}")
            
            # 콜백 함수가 있으면 실행
            if self.callback:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(data)
                else:
                    self.callback(data)
                    
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
    
    async def subscribe_ticker(self, tickers):
        """
        새로운 티커 구독 추가
        
        Args:
            tickers (list): 구독할 티커 목록
        """
        if not isinstance(tickers, list):
            tickers = [tickers]
            
        # 기존 구독 목록에 없는 티커만 추가
        new_tickers = [t for t in tickers if t not in self.tickers]
        if not new_tickers:
            return
            
        self.tickers.extend(new_tickers)
        
        # 새로운 구독 요청 전송
        if self.websocket and self.websocket.open:
            subscribe_fmt = [
                {"ticket": str(uuid.uuid4())},
                {
                    "type": "ticker",
                    "codes": self.tickers,
                    "isOnlyRealtime": True
                }
            ]
            await self.websocket.send(json.dumps(subscribe_fmt))
            self.logger.info(f"새로운 티커 구독 추가: {', '.join(new_tickers)}")
    
    def close(self):
        """
        웹소켓 연결 종료
        """
        self.running = False
        self.logger.info("웹소켓 연결 종료 요청")
        
    async def subscribe_orderbook(self, tickers):
        """
        호가창 구독
        
        Args:
            tickers (list): 구독할 티커 목록
        """
        if not isinstance(tickers, list):
            tickers = [tickers]
            
        # 구독 요청 전송
        if self.websocket and self.websocket.open:
            subscribe_fmt = [
                {"ticket": str(uuid.uuid4())},
                {
                    "type": "orderbook",
                    "codes": tickers,
                    "isOnlyRealtime": True
                }
            ]
            await self.websocket.send(json.dumps(subscribe_fmt))
            self.logger.info(f"호가창 구독 추가: {', '.join(tickers)}")
