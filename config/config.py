"""
설정 관리 모듈: 업비트 API 키와 관련 설정을 관리합니다.
"""

# 업비트 API 키 설정
# 환경 변수에서 API 키를 불러옵니다.
import os
from dotenv import load_dotenv

# .env 파일 로드 (없으면 환경 변수 사용)
load_dotenv()

# 환경 변수에서 API 키 가져오기
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

# # API 키가 설정되지 않은 경우 경고
# if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
#     print("경고: 업비트 API 키가 설정되지 않았습니다. .env 파일을 생성하거나 환경 변수를 설정해주세요.")
#     # 기본값으로 설정 (실제 사용 시 제거 필요)
#     UPBIT_ACCESS_KEY = "your_access_key_here"
#     UPBIT_SECRET_KEY = "your_secret_key_here"

# 데이터베이스 설정
DB_NAME = "crypto_trading.db"

# 로깅 설정
LOG_LEVEL = "INFO"
LOG_FILE = "crypto_trading.log"

# Slack 알림 설정
SLACK_WEBHOOK_URL = "your_slack_webhook_url_here"

# 텔레그램 알림 설정
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"

# 트레이딩 설정
MAX_TRADING_AMOUNT = 100000  # 최대 매수 금액
PROFIT_MARGIN = 0.05  # 목표 수익률 (5%)
STOP_LOSS = 0.03  # 손절 비율 (3%)
