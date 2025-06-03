"""
RSI 기반 트레이딩 전략: 상대 강도 지수를 활용한 매매 전략을 구현합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from trading.strategy.base_strategy import BaseStrategy
from config.condition import RSI_OVERSOLD, RSI_OVERBOUGHT, RSI_PERIOD
from utils.logger import Logger


class RSIStrategy(BaseStrategy):
    """
    RSI 기반 트레이딩 전략 클래스
    과매수/과매도 상태를 감지하여 매매 신호를 생성합니다.
    """
    
    def __init__(self, api, params=None):
        """
        RSI 전략 초기화
        
        Args:
            api: UpbitAPI 인스턴스
            params (dict, optional): 전략 파라미터
        """
        # 기본 파라미터 설정
        default_params = {
            'rsi_period': RSI_PERIOD,
            'oversold': RSI_OVERSOLD,
            'overbought': RSI_OVERBOUGHT,
            'interval': 'minutes',  # minutes, days, weeks, months
            'unit': 15,             # 분 단위 (1, 3, 5, 15, 30, 60, 240)
            'count': 100            # 캔들 데이터 개수
        }
        
        # 사용자 지정 파라미터로 기본값 업데이트
        if params:
            default_params.update(params)
        
        super().__init__(api, name="RSI 전략", params=default_params)
        self.logger = Logger()
    
    def should_buy(self, ticker, candles=None):
        """
        매수 신호 확인: RSI가 과매도 영역에서 반등할 때 매수 신호 생성
        
        Args:
            ticker (str): 코인 티커
            candles (pandas.DataFrame, optional): 캔들 데이터
            
        Returns:
            bool: 매수 신호 발생 여부
        """
        try:
            # 캔들 데이터가 없으면 가져오기
            if candles is None:
                candles = self.get_candles(
                    ticker, 
                    interval=self.params['interval'],
                    count=self.params['count'],
                    unit=self.params['unit']
                )
                
                if candles.empty:
                    self.logger.error(f"{ticker} 캔들 데이터를 가져오는데 실패했습니다.")
                    return False
            
            # RSI 계산
            rsi = self.calculate_rsi(candles, period=self.params['rsi_period'])
            
            # 최근 RSI 값
            current_rsi = rsi.iloc[-1]
            previous_rsi = rsi.iloc[-2]
            
            # 과매도 상태에서 반등하는 경우 매수 신호
            # RSI가 과매도 수준 이하였다가 상승하는 패턴 감지
            if previous_rsi <= self.params['oversold'] and current_rsi > previous_rsi:
                self.logger.info(
                    f"{ticker} 매수 신호 발생: RSI 과매도 반등 (RSI: {current_rsi:.2f}, 이전: {previous_rsi:.2f})"
                )
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"{ticker} 매수 신호 확인 중 오류 발생: {e}")
            return False
    
    def should_sell(self, ticker, buy_price, current_price=None, candles=None):
        """
        매도 신호 확인: RSI가 과매수 영역에 진입하거나 일정 수익률 도달 시 매도 신호 생성
        
        Args:
            ticker (str): 코인 티커
            buy_price (float): 매수 가격
            current_price (float, optional): 현재 가격
            candles (pandas.DataFrame, optional): 캔들 데이터
            
        Returns:
            bool: 매도 신호 발생 여부
        """
        try:
            # 캔들 데이터가 없으면 가져오기
            if candles is None:
                candles = self.get_candles(
                    ticker, 
                    interval=self.params['interval'],
                    count=self.params['count'],
                    unit=self.params['unit']
                )
                
                if candles.empty:
                    self.logger.error(f"{ticker} 캔들 데이터를 가져오는데 실패했습니다.")
                    return False
            
            # 현재 가격이 제공되지 않았으면 마지막 캔들의 종가 사용
            if current_price is None:
                current_price = candles['close'].iloc[-1]
            
            # RSI 계산
            rsi = self.calculate_rsi(candles, period=self.params['rsi_period'])
            
            # 최근 RSI 값
            current_rsi = rsi.iloc[-1]
            
            # 수익률 계산
            profit_rate = (current_price / buy_price - 1) * 100
            
            # 1. RSI 과매수 조건 확인
            if current_rsi >= self.params['overbought']:
                self.logger.info(
                    f"{ticker} 매도 신호 발생: RSI 과매수 상태 (RSI: {current_rsi:.2f}, 수익률: {profit_rate:.2f}%)"
                )
                return True
            
            # 2. 손절 조건 (5% 이상 손실)
            if profit_rate <= -5:
                self.logger.info(
                    f"{ticker} 매도 신호 발생: 손절 조건 충족 (수익률: {profit_rate:.2f}%)"
                )
                return True
            
            # 3. 큰 수익 실현 조건 (10% 이상 수익)
            if profit_rate >= 10:
                self.logger.info(
                    f"{ticker} 매도 신호 발생: 수익 실현 조건 충족 (수익률: {profit_rate:.2f}%)"
                )
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"{ticker} 매도 신호 확인 중 오류 발생: {e}")
            return False
    
    def get_current_signal(self, ticker):
        """
        현재 매매 신호 상태 확인
        
        Args:
            ticker (str): 코인 티커
            
        Returns:
            dict: 매매 신호 정보
        """
        try:
            candles = self.get_candles(
                ticker, 
                interval=self.params['interval'],
                count=self.params['count'],
                unit=self.params['unit']
            )
            
            if candles.empty:
                return {'signal': 'UNKNOWN', 'rsi': None, 'price': None}
            
            # RSI 계산
            rsi = self.calculate_rsi(candles, period=self.params['rsi_period'])
            current_rsi = rsi.iloc[-1]
            current_price = candles['close'].iloc[-1]
            
            # 신호 판단
            signal = 'HOLD'
            if current_rsi <= self.params['oversold']:
                signal = 'BUY'
            elif current_rsi >= self.params['overbought']:
                signal = 'SELL'
                
            return {
                'signal': signal,
                'rsi': current_rsi,
                'price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"{ticker} 현재 신호 확인 중 오류 발생: {e}")
            return {'signal': 'ERROR', 'rsi': None, 'price': None}
