"""
업비트 암호화폐 거래 시스템 설정 파일
"""
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 업비트 API 키
UPBIT_ACCESS_KEY = os.environ.get('UPBIT_ACCESS_KEY', '')

# 데이터베이스 설정
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_DATABASE', 'crypto_trading')

# 웹소켓 URL
UPBIT_WS_URL = "wss://api.upbit.com/websocket/v1"

# API URL
UPBIT_API_URL = "https://api.upbit.com"

# API 요청 시간 제한 (초)
API_TIMEOUT = 10

# 토큰 갱신 시간 (초)
TOKEN_REFRESH_INTERVAL = 86400  # 24시간

# API 요청 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 5