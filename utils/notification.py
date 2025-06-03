"""
uc54cub9bc uc720ud2f8ub9acud2f0 ubaa8ub4c8: uc2acub799, ud154ub808uadf8ub7a8 ub4f1uc744 ud1b5ud55c uc54cub9bc uae30ub2a5uc744 uc81cuacf5ud569ub2c8ub2e4.
"""

import json
import requests
import logging
from datetime import datetime
from config.config import SLACK_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.logger import Logger


class Notifier:
    """ub2e4uc591ud55c ucc44ub110uc744 ud1b5ud55c uc54cub9bc uae30ub2a5uc744 uc81cuacf5ud558ub294 ud074ub798uc2a4"""
    
    def __init__(self):
        """
Notifier ud074ub798uc2a4 ucd08uae30ud654
        """
        self.logger = Logger()
        self.slack_webhook_url = SLACK_WEBHOOK_URL
        self.telegram_bot_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
    
    def send_slack_message(self, message, attachments=None):
        """
        uc2acub799uc73cub85c uba54uc2dcuc9c0 uc804uc1a1
        
        Args:
            message (str): uc804uc1a1ud560 uba54uc2dcuc9c0
            attachments (list, optional): ucca8ubd80ud560 uc815ubcf4 ubaa9ub85d
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        if not self.slack_webhook_url or self.slack_webhook_url == "your_slack_webhook_url_here":
            self.logger.warning("uc2acub799 uc6f9ud6c4ud06c URLuc774 uc124uc815ub418uc9c0 uc54auc544 uc54cub9bcuc774 uc804uc1a1ub418uc9c0 uc54auc558uc2b5ub2c8ub2e4.")
            return False
        
        try:
            payload = {
                "text": message,
                "username": "Crypto Trading Bot",
                "icon_emoji": ":chart_with_upwards_trend:"
            }
            
            if attachments:
                payload["attachments"] = attachments
            
            response = requests.post(
                self.slack_webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.logger.error(f"uc2acub799 uc54cub9bc uc804uc1a1 uc2e4ud328: {response.status_code} - {response.text}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"uc2acub799 uc54cub9bc uc804uc1a1 uc911 uc624ub958 ubc1cuc0dd: {e}")
            return False
    
    def send_telegram_message(self, message):
        """
        ud154ub808uadf8ub7a8uc73cub85c uba54uc2dcuc9c0 uc804uc1a1
        
        Args:
            message (str): uc804uc1a1ud560 uba54uc2dcuc9c0
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        if not self.telegram_bot_token or self.telegram_bot_token == "your_telegram_bot_token_here" or \
           not self.telegram_chat_id or self.telegram_chat_id == "your_telegram_chat_id_here":
            self.logger.warning("ud154ub808uadf8ub7a8 ud1a0ud070 ub610ub294 ucc44ud305 IDuac00 uc124uc815ub418uc9c0 uc54auc544 uc54cub9bcuc774 uc804uc1a1ub418uc9c0 uc54auc558uc2b5ub2c8ub2e4.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            params = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, params=params)
            
            if response.status_code != 200:
                self.logger.error(f"ud154ub808uadf8ub7a8 uc54cub9bc uc804uc1a1 uc2e4ud328: {response.status_code} - {response.text}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"ud154ub808uadf8ub7a8 uc54cub9bc uc804uc1a1 uc911 uc624ub958 ubc1cuc0dd: {e}")
            return False
    
    def send_notification(self, message, level="INFO", data=None, use_slack=True, use_telegram=False):
        """
        uc5ecub7ec ucc44ub110uc744 ud1b5ud55c uc54cub9bc uc804uc1a1
        
        Args:
            message (str): uc54cub9bc uba54uc2dcuc9c0
            level (str): uc54cub9bc ub808ubca8 ('INFO', 'WARNING', 'ERROR')
            data (dict, optional): ucd94uac00 ub370uc774ud130
            use_slack (bool): uc2acub799 uc54cub9bc uc0acuc6a9 uc5ecubd80
            use_telegram (bool): ud154ub808uadf8ub7a8 uc54cub9bc uc0acuc6a9 uc5ecubd80
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        # ub85cuadf8 uae30ub85d
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
        
        success = True
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # uc2acub799 uc54cub9bc uc804uc1a1
        if use_slack:
            emoji = ":information_source:" if level == "INFO" else \
                   ":warning:" if level == "WARNING" else \
                   ":x:" if level == "ERROR" else \
                   ":bell:"
            
            slack_message = f"*{level}* | {timestamp}\n{message}"
            
            attachments = None
            if data:
                attachments = [{
                    "color": "#36a64f" if level == "INFO" else \
                              "#ffcc00" if level == "WARNING" else \
                              "#ff0000" if level == "ERROR" else \
                              "#439FE0",
                    "fields": [{
                        "title": key,
                        "value": str(value),
                        "short": True
                    } for key, value in data.items()]
                }]
            
            if not self.send_slack_message(slack_message, attachments):
                success = False
        
        # ud154ub808uadf8ub7a8 uc54cub9bc uc804uc1a1
        if use_telegram:
            telegram_message = f"*{level}* | {timestamp}\n{message}"
            
            if data:
                telegram_message += "\n\n*\uc0c1uc138 uc815ubcf4:*"
                for key, value in data.items():
                    telegram_message += f"\nu2022 *{key}*: {value}"
            
            if not self.send_telegram_message(telegram_message):
                success = False
        
        return success
    
    def notify_trade(self, action, ticker, price, amount, order_id=None):
        """
        uac70ub798 uc54cub9bc uc804uc1a1
        
        Args:
            action (str): uac70ub798 uc720ud615 ('BUY', 'SELL')
            ticker (str): ucf54uc778 ud2f0ucee4
            price (float): uac00uaca9
            amount (float): uc218ub7c9 ub610ub294 uae08uc561
            order_id (str, optional): uc8fcubb38 ID
            
        Returns:
            bool: uc131uacf5 uc5ecubd80
        """
        action_kr = "ub9e4uc218" if action == "BUY" else "ub9e4ub3c4"
        message = f"{ticker} {action_kr} uc8fcubb38 uc131uacf5"
        
        data = {
            "ucf54uc778": ticker,
            "uac00uaca9": f"{price:,} KRW",
            "uc218ub7c9/uae08uc561": amount
        }
        
        if order_id:
            data["uc8fcubb38ID"] = order_id
            
        return self.send_notification(message, data=data, use_telegram=(action=="SELL"))
