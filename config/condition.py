"""
거래 조건 관련 상수 정의 모듈: 트레이딩에 필요한 조건값들을 정의합니다.
"""

# 트레이딩 시간 설정
TRADING_START_HOUR = None  # None일 경우 24시간 트레이딩
TRADING_END_HOUR = None  # None일 경우 24시간 트레이딩
# TRADING_START_HOUR = 9  # 트레이딩 시작 시간 (9시)
# TRADING_END_HOUR = 23  # 트레이딩 종료 시간 (23시)

# 스케줄러 간격 설정 (분)
MARKET_CHECK_INTERVAL = 15  # 시장 체크 간격 (분)
TRADE_INTERVAL = 30  # 트레이딩 사이클 실행 간격 (분)
ORDER_CHECK_INTERVAL = 5  # 미체결 주문 확인 간격 (분)

# 스케줄러 설정 (시간, 분)
MARKET_CHECK_HOUR = 9  # 시장 분석 시간 (시)
MARKET_CHECK_MINUTE = 0  # 시장 분석 시간 (분)
TRADING_HOUR = 9  # 매매 실행 시간 (시)
TRADING_MINUTE = 30  # 매매 실행 시간 (분)

# 주문 관련 설정
BUY_WAIT = 3  # 매수 후 대기 시간 (초)
SELL_WAIT = 3  # 매도 후 대기 시간 (초)
WAIT_TIME_ORDER_COMPLETE = 60  # 주문 완료 대기 시간 (초)
WAIT_TIME_BUY_CANCEL = 300  # 매수 주문 취소 대기 시간 (초)
WAIT_TIME_SELL_CANCEL = 600  # 매도 주문 취소 대기 시간 (초)
MAX_RETRIES = 3  # 최대 재시도 횟수

# 매매 전략 설정
VOLUME_THRESHOLD = 100000000  # 거래량 기준 (1억 원)
PRICE_CHANGE_THRESHOLD = 5.0  # 가격 변동 기준 (5%)
VOLATILITY_THRESHOLD = 3.0  # 변동성 기준 (3%)

# 포트폴리오 설정
MAX_COINS = 5  # 최대 보유 코인 종류 수
POSITION_SIZE = 0.2  # 각 코인별 자산 배분 비율 (총 자산의 20%)

# RSI 지표 설정
RSI_PERIOD = 14  # RSI 계산 기간
RSI_OVERSOLD = 30  # 과매도 기준
RSI_OVERBOUGHT = 70  # 과매수 기준

# 이동평균선 설정
MA_SHORT = 7  # 단기 이동평균선 기간
MA_LONG = 25  # 장기 이동평균선 기간
