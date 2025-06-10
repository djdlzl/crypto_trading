"""
거래 조건 설정 모듈

매수 및 매도 조건에 관한 설정을 정의합니다.
"""

# 매도 조건: 평균 매수가 대비 상승 시 익절 포인트
SELLING_POINT_UPPER = 1.05  # 5% 이상 상승 시 매도

# 리스크 관리: 평균 매수가 대비 하락 시 손절 포인트
RISK_MGMT_LOWER = 0.95  # 5% 이상 하락 시 손절

# 투자 금액 제한
MAX_INVESTMENT_PER_COIN = 100000  # 코인당 최대 투자 금액 (원)
TOTAL_INVESTMENT_LIMIT = 1000000  # 총 투자 금액 한도 (원)

# 거래 수수료 (퍼센트)
TRADING_FEE = 0.05

# 최소 거래 간격 (초)
MIN_TRADE_INTERVAL = 300  # 5분

# 모니터링 주기 (초)
MONITORING_INTERVAL = 10

# 시장 분석을 위한 이동평균선 기간
SHORT_MA_PERIOD = 5
MIDDLE_MA_PERIOD = 20
LONG_MA_PERIOD = 60

# 볼린저 밴드 설정
BOLLINGER_WINDOW = 20
BOLLINGER_STD_DEV = 2

# RSI 지표 설정
RSI_PERIOD = 14
RSI_OVERSOLD = 30  # RSI가 이 값보다 낮으면 과매도 상태로 판단
RSI_OVERBOUGHT = 70  # RSI가 이 값보다 높으면 과매수 상태로 판단