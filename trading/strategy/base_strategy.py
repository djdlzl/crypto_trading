"""
uae30ubcf8 ud2b8ub808uc774ub529 uc804ub7b5 ubaa8ub4c8: ubaa8ub4e0 ud2b8ub808uc774ub529 uc804ub7b5uc774 uc0c1uc18dud558ub294 uae30ubcf8 ud074ub798uc2a4ub97c uc815uc758ud569ub2c8ub2e4.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from utils.logger import Logger


class BaseStrategy(ABC):
    """
    ud2b8ub808uc774ub529 uc804ub7b5uc744 uc704ud55c uae30ubcf8 ucd94uc0c1 ud074ub798uc2a4
    uc774 ud074ub798uc2a4ub97c uc0c1uc18dud558uc5ec ub2e4uc591ud55c ud2b8ub808uc774ub529 uc804ub7b5uc744 uad6cud604ud560 uc218 uc788uc2b5ub2c8ub2e4.
    """
    
    def __init__(self, api, name=None, params=None):
        """
        BaseStrategy ud074ub798uc2a4 ucd08uae30ud654
        
        Args:
            api: API ud074ub798uc2a4 uc778uc2a4ud134uc2a4 (UpbitAPI)
            name (str, optional): uc804ub7b5 uc774ub984
            params (dict, optional): uc804ub7b5 ud30cub77cubbf8ud130
        """
        self.api = api
        self.name = name or self.__class__.__name__
        self.params = params or {}
        self.logger = Logger()
    
    @abstractmethod
    def should_buy(self, ticker, candles=None):
        """
        ub9e4uc218 uc2e0ud638 ud655uc778
        
        Args:
            ticker (str): ucf54uc778 ud2f0ucee4
            candles (list, optional): uce94ub4e4 ub370uc774ud130
            
        Returns:
            bool: ub9e4uc218 uc2e0ud638 ubc1cuc0dd uc5ecubd80
        """
        pass
    
    @abstractmethod
    def should_sell(self, ticker, buy_price, current_price=None, candles=None):
        """
        ub9e4ub3c4 uc2e0ud638 ud655uc778
        
        Args:
            ticker (str): ucf54uc778 ud2f0ucee4
            buy_price (float): ub9e4uc218 uac00uaca9
            current_price (float, optional): ud604uc7ac uac00uaca9
            candles (list, optional): uce94ub4e4 ub370uc774ud130
            
        Returns:
            bool: ub9e4ub3c4 uc2e0ud638 ubc1cuc0dd uc5ecubd80
        """
        pass
    
    def get_candles(self, ticker, interval='minutes', count=200, unit=1):
        """
        uce94ub4e4 ub370uc774ud130 uc870ud68c
        
        Args:
            ticker (str): ucf54uc778 ud2f0ucee4
            interval (str): uc2dcuac04 uac04uaca9 ('minutes', 'days', 'weeks', 'months')
            count (int): ub370uc774ud130 uac1cuc218
            unit (int): uc2dcuac04 ub2e8uc704
            
        Returns:
            pandas.DataFrame: uce94ub4e4 ub370uc774ud130
        """
        try:
            candles = self.api.get_candles(ticker, interval, count, unit)
            
            # pandas DataFrameuc73cub85c ubcc0ud658
            df = pd.DataFrame(candles)
            
            # uceecub7fc uc774ub984 ubcc0uacbd
            df = df.rename(columns={
                'opening_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'trade_price': 'close',
                'candle_acc_trade_volume': 'volume',
                'candle_date_time_kst': 'datetime'
            })
            
            # ub370uc774ud130 ud615uc2dd ubcc0ud658
            df['datetime'] = pd.to_datetime(df['datetime'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col])
            
            # uc2dcuac04uc21c uc815ub82c
            df = df.sort_values('datetime')
            
            return df
            
        except Exception as e:
            self.logger.error(f"uce94ub4e4 ub370uc774ud130 uc870ud68c uc911 uc624ub958 ubc1cuc0dd: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, df, period=14):
        """
        RSI(Relative Strength Index) uacc4uc0b0
        
        Args:
            df (pandas.DataFrame): uce94ub4e4 ub370uc774ud130
            period (int): RSI uacc4uc0b0 uae30uac04
            
        Returns:
            pandas.Series: RSI uac12
        """
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        """
        MACD(Moving Average Convergence Divergence) uacc4uc0b0
        
        Args:
            df (pandas.DataFrame): uce94ub4e4 ub370uc774ud130
            fast (int): ube60ub978 EMA uae30uac04
            slow (int): ub290ub9b0 EMA uae30uac04
            signal (int): uc2dcuadf8ub110 uae30uac04
            
        Returns:
            tuple: (MACD, Signal, Histogram)
        """
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal
        
        return macd, signal, histogram
    
    def calculate_bollinger_bands(self, df, window=20, num_std=2):
        """
        ubcfcub9b0uc800 ubc34ub4dc uacc4uc0b0
        
        Args:
            df (pandas.DataFrame): uce94ub4e4 ub370uc774ud130
            window (int): uc774ub3d9ud3c9uade0 uae30uac04
            num_std (int): ud45cuc900ud3b8ucc28 uacc4uc218
            
        Returns:
            tuple: (Upper Band, Middle Band, Lower Band)
        """
        rolling_mean = df['close'].rolling(window=window).mean()
        rolling_std = df['close'].rolling(window=window).std()
        
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        
        return upper_band, rolling_mean, lower_band
    
    def calculate_ma(self, df, windows=[5, 10, 20, 60, 120]):
        """
        uc5ecub7ec uae30uac04uc758 uc774ub3d9ud3c9uade0 uacc4uc0b0
        
        Args:
            df (pandas.DataFrame): uce94ub4e4 ub370uc774ud130
            windows (list): uc774ub3d9ud3c9uade0 uae30uac04 ubaa9ub85d
            
        Returns:
            dict: uae30uac04ubcc4 uc774ub3d9ud3c9uade0
        """
        ma_dict = {}
        for window in windows:
            ma_dict[f'MA{window}'] = df['close'].rolling(window=window).mean()
        
        return ma_dict
    
    def calculate_volume_profile(self, df, bins=10):
        """
        ubcfcub968 ud504ub85cud30cuc77c uacc4uc0b0
        
        Args:
            df (pandas.DataFrame): uce94ub4e4 ub370uc774ud130
            bins (int): uac00uaca9 uad6cuac04 uc218
            
        Returns:
            pandas.DataFrame: ubcfcub968 ud504ub85cud30cuc77c
        """
        min_price = df['low'].min()
        max_price = df['high'].max()
        price_range = max_price - min_price
        
        # uac00uaca9 uad6cuac04 uc0dduc131
        price_bins = [min_price + (price_range / bins) * i for i in range(bins + 1)]
        
        # uac01 uac00uaca9 uad6cuac04ubcc4 ubc88ub960 uacc4uc0b0
        volume_profile = pd.DataFrame(columns=['price_mid', 'volume'])
        
        for i in range(bins):
            lower_bound = price_bins[i]
            upper_bound = price_bins[i + 1]
            price_mid = (lower_bound + upper_bound) / 2
            
            # ud574ub2f9 uac00uaca9 uad6cuac04uc5d0 ud3ecud568ub418ub294 uac70ub798ub7c9 ud569uacc4
            vol_in_bin = df[(df['low'] <= upper_bound) & (df['high'] >= lower_bound)]['volume'].sum()
            
            volume_profile = volume_profile.append({
                'price_mid': price_mid,
                'volume': vol_in_bin
            }, ignore_index=True)
        
        return volume_profile
