
import yfinance as yf
import pandas as pd
from typing import List, Dict
import numpy as np

class TimeAndSalesAnalyzer:
    """Analyze Time & Sales data for large prints and aggressive activity"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
    
    def get_time_and_sales(self, period: str = '1d') -> pd.DataFrame:
        """
        Fetch intraday tick data (approximation using 1-min bars)
        """
        stock = yf.Ticker(self.ticker)
        data = stock.history(period=period, interval='1m')
        
        if data.empty:
            return pd.DataFrame()

        # Calculate features
        data['trade_size'] = data['Volume']
        data['price'] = data['Close']
        data['aggressive'] = self._detect_aggressive_trading(data)
        
        return data
    
    def _detect_aggressive_trading(self, data: pd.DataFrame) -> pd.Series:
        """
        Detect aggressive buying/selling
        """
        # Calculate where close is in the range (0 = low, 1 = high)
        denom = (data['High'] - data['Low'])
        # Avoid division by zero
        denom = denom.replace(0, 0.01) 
        
        close_position = (data['Close'] - data['Low']) / denom
        
        # Aggressive if close is at extreme + high volume
        vol_threshold = data['Volume'].quantile(0.75)
        
        aggressive = []
        for idx, row in data.iterrows():
            if row['Volume'] > vol_threshold:
                pos = close_position[idx]
                if pos > 0.8:
                    aggressive.append('BUY')
                elif pos < 0.2:
                    aggressive.append('SELL')
                else:
                    aggressive.append('NEUTRAL')
            else:
                aggressive.append('NEUTRAL')
        
        return pd.Series(aggressive, index=data.index)
    
    def find_large_prints(self, threshold_multiplier: float = 2.0) -> List[Dict]:
        """
        Find unusually large trades (block trades)
        """
        data = self.get_time_and_sales()
        
        if data.empty: return []

        # Calculate threshold
        avg_volume = data['Volume'].mean()
        threshold = avg_volume * threshold_multiplier
        
        # Find large prints
        large_prints = data[data['Volume'] > threshold].copy()
        
        results = []
        for idx, row in large_prints.iterrows():
            results.append({
                'time': idx.strftime('%H:%M'), # Format time
                'price': row['price'],
                'size': row['Volume'],
                'size_vs_avg': row['Volume'] / avg_volume if avg_volume > 0 else 0,
                'aggressive': row['aggressive'],
                'interpretation': self._interpret_large_print(row)
            })
        
        return results
    
    def _interpret_large_print(self, row) -> str:
        """Interpret what a large print means"""
        agg = row['aggressive']
        if agg == 'BUY':
            return "🟢 Large aggressive BUYING - Institutions accumulating"
        elif agg == 'SELL':
            return "🔴 Large aggressive SELLING - Institutions distributing"
        else:
            return "⚪ Large neutral print - Likely block trade"
    
    def analyze_activity_at_level(self, price_level: float, tolerance_pct: float = 0.1) -> Dict:
        """
        Analyze Time & Sales activity at a specific price level
        """
        data = self.get_time_and_sales()
        
        if data.empty:
            return {'status': 'NO_DATA', 'level': price_level}

        # Filter trades near the level
        tolerance = price_level * (tolerance_pct / 100)
        level_trades = data[
            (data['price'] >= price_level - tolerance) & 
            (data['price'] <= price_level + tolerance)
        ]
        
        if len(level_trades) == 0:
            return {'status': 'NO_ACTIVITY', 'level': price_level}
        
        # Analyze the activity
        total_volume = level_trades['Volume'].sum()
        buy_volume = level_trades[level_trades['aggressive'] == 'BUY']['Volume'].sum()
        sell_volume = level_trades[level_trades['aggressive'] == 'SELL']['Volume'].sum()
        neutral_volume = total_volume - buy_volume - sell_volume
        
        # Calculate ratios
        buy_ratio = buy_volume / total_volume if total_volume > 0 else 0
        sell_ratio = sell_volume / total_volume if total_volume > 0 else 0
        
        # Determine bias
        if buy_ratio > 0.6:
            bias = 'BULLISH'
            interpretation = f"Strong buying at ${price_level:.2f} - Level likely to hold as support"
        elif sell_ratio > 0.6:
            bias = 'BEARISH'
            interpretation = f"Strong selling at ${price_level:.2f} - Level likely to act as resistance"
        else:
            bias = 'NEUTRAL'
            interpretation = f"Balanced activity at ${price_level:.2f} - No clear bias"
        
        return {
            'status': 'ACTIVE',
            'level': price_level,
            'total_volume': int(total_volume),
            'buy_volume': int(buy_volume),
            'sell_volume': int(sell_volume),
            'neutral_volume': int(neutral_volume),
            'buy_ratio': buy_ratio,
            'sell_ratio': sell_ratio,
            'bias': bias,
            'interpretation': interpretation,
            'num_trades': len(level_trades)
        }
    
    def scan_key_levels(self, poc: float, vah: float, val: float) -> Dict:
        """Scan all key levels for activity"""
        return {
            'poc': self.analyze_activity_at_level(poc),
            'vah': self.analyze_activity_at_level(vah),
            'val': self.analyze_activity_at_level(val)
        }
