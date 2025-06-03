# Crypto Trading Bot

## 프로젝트 개요
이 프로젝트는 업비트(Upbit) 거래소의 API와 웹소켓을 활용하여 암호화폐 자동 매매를 수행하는 트레이딩 봇입니다. 다양한 전략(예: RSI 기반 전략)과 스케줄러를 통해 자동으로 거래를 실행하며, 데이터베이스 연동, 알림, 로깅 등 실전 운용에 필요한 기능을 포함합니다.

## 디렉터리 구조
```
crypto_trading/
├── api/                 # 외부 거래소 API 및 웹소켓 연동 모듈
│   ├── upbit_api.py
│   └── upbit_websocket.py
├── config/              # 환경설정 및 조건 관련 파일
│   ├── condition.py
│   └── config.py
├── database/            # 데이터베이스 관리 모듈
│   └── db_manager.py
├── main.py              # 트레이딩 봇 메인 실행 파일
├── requirements.txt     # 프로젝트 의존성 패키지 목록
├── tests/               # 테스트 코드
├── tmp.py               # 임시 스크립트 (gitignore 처리됨)
├── trading/             # 트레이딩 로직 및 전략 구현
│   ├── strategy/
│   │   ├── base_strategy.py
│   │   └── rsi_strategy.py
│   └── trading_logic.py
├── utils/               # 유틸리티 및 공통 기능
│   ├── logger.py
│   └── notification.py
└── venv/                # 가상환경(버전관리 제외)
```

## 주요 기능
- 업비트 REST API 및 웹소켓 연동
- 자동 매매 전략(예: RSI)
- 스케줄러 기반 주기적 거래 실행
- 거래 내역, 로그, 알림 관리
- 환경설정 및 조건별 거래 시간 제어

## 설치 및 실행 방법
```bash
# 패키지 설치
pip install -r requirements.txt

# 메인 봇 실행
python main.py
```

## 앞으로의 개발 계획
- 다양한 매매 전략 추가 (예: 이동평균선, 볼린저밴드 등)
- 백테스팅 및 시뮬레이션 기능 강화
- 웹 대시보드/모니터링 시스템 연동
- 코드 리팩토링 및 테스트 커버리지 확대
- 실거래 안전장치 및 예외처리 강화

## 기여 방법
1. 이슈 등록 또는 PR 요청
2. 코드 작성 시 PEP8 스타일 가이드 준수
3. 함수/클래스별 주석 및 문서화

## 라이선스
MIT License

---
문의 및 피드백은 이슈 또는 PR로 남겨주세요.
