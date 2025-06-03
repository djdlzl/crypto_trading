"""
로깅 유틸리티 모듈: 애플리케이션 로그를 관리하는 클래스를 정의합니다.
"""

import logging
import os
from datetime import datetime
from config.config import LOG_LEVEL, LOG_FILE


class Logger:
    """로깅 관리 클래스"""
    
    _instance = None  # 싱글톤 패턴을 위한 인스턴스 저장 변수
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """로거 초기화"""
        # 로그 디렉토리 생성
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일 경로 설정
        log_file = os.path.join(log_dir, LOG_FILE)
        
        # 로거 설정
        self.logger = logging.getLogger('crypto_trading')
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # 이미 핸들러가 있는 경우 중복 방지
        if not self.logger.handlers:
            # 파일 핸들러 추가
            file_handler = logging.FileHandler(log_file)
            file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
            
            # 콘솔 핸들러 추가
            console_handler = logging.StreamHandler()
            console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
    
    def debug(self, message):
        """디버그 로그 기록"""
        self.logger.debug(message)
    
    def info(self, message):
        """정보 로그 기록"""
        self.logger.info(message)
    
    def warning(self, message):
        """경고 로그 기록"""
        self.logger.warning(message)
    
    def error(self, message):
        """에러 로그 기록"""
        self.logger.error(message)
    
    def critical(self, message):
        """심각한 에러 로그 기록"""
        self.logger.critical(message)
