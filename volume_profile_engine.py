"""
Volume Profile Engine - Core Calculations
Modular design for AI agent integration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, List, Optional
import yfinance as yf


class VolumeProfileEngine:
    """
    Core engine for Volume Profile calculations.
    """
    
    def __init__(self, ticker: str = None, period: str = "1mo", interval: str = "15m", data: pd.DataFrame = None):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data = data
        self.volume_profile = None
        
    def fetch_data(self) -> pd.DataFrame:
        """Fetches historical data from yfinance if not provided."""
        if self.data is not None and not self.data.empty:
            return self.data
            
        if not self.ticker:
            return pd.DataFrame()
            
        ticker_obj = yf.Ticker(self.ticker)
        # Handle interval mapping for yfinance
        yf_interval = self.interval
        if self.interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']:
            pass
        else:
            yf_interval = '1d' # default
            
        self.data = ticker_obj.history(period=self.period, interval=yf_interval)
        return self.data

    def calculate_volume_profile(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """Calculates volume profile."""
        if data is not None:
             self.data = data

        if self.data is None or self.data.empty:
            self.fetch_data()
            
        if self.data.empty:
            self.volume_profile = pd.DataFrame()
            return self.volume_profile
            
        # Basic calculation
        price_min = self.data['Low'].min()
        price_max = self.data['High'].max()
        
        # 100 bins
        bins = np.linspace(price_min, price_max, 101)
        
        # Histogram
        # Using numpy histogram
        vol_hist, bin_edges = np.histogram(self.data['Close'], bins=bins, weights=self.data['Volume'])
        
        # Create DF
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        self.volume_profile = pd.DataFrame({'price': bin_centers, 'volume': vol_hist})
        
        return self.volume_profile

    def find_poc(self, profile: pd.DataFrame) -> float:
        """Finds the Point of Control (POC)."""
        if profile.empty:
            return 0.0
        idx = profile['volume'].idxmax()
        return profile.loc[idx, 'price']

    def find_value_area(self, profile: pd.DataFrame, va_pct: float = 0.70) -> Tuple[float, float]:
        """Finds Value Area High (VAH) and Value Area Low (VAL)."""
        if profile.empty:
            return 0.0, 0.0
            
        total_vol = profile['volume'].sum()
        target = total_vol * va_pct
        sorted_prof = profile.sort_values('volume', ascending=False)
        
        cum = 0
        va_prices = []
        for _, row in sorted_prof.iterrows():
            cum += row['volume']
            va_prices.append(row['price'])
            if cum >= target: break
            
        if not va_prices:
            return 0.0, 0.0
            
        vah = max(va_prices)
        val = min(va_prices)
        return val, vah

    def get_all_metrics(self) -> Dict:
        """Get POC, VAH, VAL."""
        if self.volume_profile is None:
            self.calculate_volume_profile()
            
        if self.volume_profile.empty:
            return {'poc': 0.0, 'vah': 0.0, 'val': 0.0}
            
        # POC
        poc = self.find_poc(self.volume_profile)
        
        # VA
        val, vah = self.find_value_area(self.volume_profile)
        
        if self.data is not None and not self.data.empty:
            current_price = self.data['Close'].iloc[-1]
        else:
            current_price = 0.0

        # Position Logic
        if current_price > vah:
            position = "ABOVE VALUE"
        elif current_price < val:
            position = "BELOW VALUE"
        else:
            position = "INSIDE VALUE"

        # Distance
        dist = 0.0
        if poc != 0:
            dist = ((current_price - poc) / poc) * 100

        total_vol = self.volume_profile['volume'].sum()

        # VA Width
        va_width = vah - val
        va_width_pct = (va_width / poc * 100) if poc != 0 else 0

        return {
            'poc': poc,
            'vah': vah,
            'val': val,
            'va_width': va_width,
            'va_width_pct': va_width_pct,
            'current_price': current_price,
            'position': position,
            'distance_from_poc_pct': dist,
            'volume_traded': total_vol,
            'total_volume': int(total_vol)
        }

    def get_daily_profiles(self, days: int = 5) -> List[Dict]:
        """
        Calculates volume profiles for the last N days.
        Returns a list of dictionaries, each containing profile data for a day.
        """
        if not self.ticker:
            return []
            
        full_period = f"{days+5}d"
        engine = VolumeProfileEngine(self.ticker, period=full_period, interval='1h')
        data = engine.fetch_data()
        
        if data.empty:
            return []
            
        dates = sorted(list(set(data.index.date)))
        target_dates = dates[-days:]
        
        profiles = []
        for d in target_dates:
            day_data = data[data.index.date == d]
            if day_data.empty: continue
            
            eng = VolumeProfileEngine(data=day_data)
            m = eng.get_all_metrics()
            
            profiles.append({
                'date': d,
                'poc': m['poc'],
                'vah': m['vah'],
                'val': m['val']
            })
            
        return profiles

# --- PRIORITY FEATURES CLASSES (Inserted based on User Guide) ---

class ProfileComparator:
    """Compare profiles across different time periods"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
    
    def compare_yesterday_today(self) -> Dict:
        """
        Compare yesterday's profile with today's
        """
        # Get today's profile
        today_engine = VolumeProfileEngine(self.ticker, period='1d', interval='5m')
        today_metrics = today_engine.get_all_metrics()
        
        # Get yesterday's profile
        # Trick: fetch 5 days, take the 2nd to last day
        yesterday_engine = VolumeProfileEngine(self.ticker, period='5d', interval='5m')
        data = yesterday_engine.fetch_data()
        
        if data.empty:
            return {}
            
        # Group by date
        dates = sorted(list(set(data.index.date)))
        if len(dates) < 2:
            return {'error': 'Not enough data for comparison'}
            
        yest_date = dates[-2]
        yest_data = data[data.index.date == yest_date]
        
        y_engine = VolumeProfileEngine(data=yest_data)
        yesterday_metrics = y_engine.get_all_metrics()
        
        # Calculate shifts
        if yesterday_metrics['poc'] == 0:
            return {'error': 'Yesterday POC is 0'}
            
        poc_shift = ((today_metrics['poc'] - yesterday_metrics['poc']) / yesterday_metrics['poc']) * 100
        vah_shift = ((today_metrics['vah'] - yesterday_metrics['vah']) / yesterday_metrics['vah']) * 100
        val_shift = ((today_metrics['val'] - yesterday_metrics['val']) / yesterday_metrics['val']) * 100
        
        # Determine direction
        avg_shift = (poc_shift + vah_shift + val_shift) / 3
        if avg_shift > 0.2: # Threshold
            direction = 'UP'
        elif avg_shift < -0.2:
            direction = 'DOWN'
        else:
            direction = 'STABLE'
        
        return {
            'today': today_metrics,
            'yesterday': yesterday_metrics,
            'shift': {
                'poc_shift_pct': poc_shift,
                'vah_shift_pct': vah_shift,
                'val_shift_pct': val_shift,
                'direction': direction,
                'interpretation': self._interpret_shift(direction, avg_shift)
            }
        }
    
    def _interpret_shift(self, direction: str, shift_pct: float) -> str:
        """Interpret what the shift means"""
        if direction == 'UP':
            return f"Bullish migration: Value moving {abs(shift_pct):.2f}% higher"
        elif direction == 'DOWN':
            return f"Bearish migration: Value moving {abs(shift_pct):.2f}% lower"
        else:
            return "Stable: Value area balanced, no significant shift"


class ValueAreaMigrationTracker:
    """Track value area movement over time"""
    
    def __init__(self, ticker: str, lookback_days: int = 10):
        self.ticker = ticker
        self.lookback_days = lookback_days
    
    def track_migration(self) -> Dict:
        """
        Track VA migration over last N days
        """
        # Efficient fetch: get N days data once
        # Using 1h bars for daily profiles approximation
        full_period = f"{self.lookback_days + 5}d"
        engine = VolumeProfileEngine(self.ticker, period=full_period, interval='1h')
        data = engine.fetch_data()
        
        if data.empty: return {}
        
        # Split by day
        dates = sorted(list(set(data.index.date)))
        dates = dates[-self.lookback_days:]
        
        history = []
        
        for d in dates:
            day_data = data[data.index.date == d]
            if day_data.empty: continue
            
            d_engine = VolumeProfileEngine(data=day_data)
            m = d_engine.get_all_metrics()
            history.append({
                'date': d.strftime('%Y-%m-%d'),
                'poc': m['poc'],
                'vah': m['vah'],
                'val': m['val'],
                'va_midpoint': (m['vah'] + m['val']) / 2
            })
            
        # Calculate trend
        trend_data = self._calculate_trend(history)
        
        return {
            'history': history,
            'trend': trend_data['trend'],
            'velocity': trend_data['velocity'],
            'context': trend_data['context'],
            'strength': trend_data['strength'],
            'visual_indicator': '↑' if trend_data['trend'] == 'UPTREND' else '↓' if trend_data['trend'] == 'DOWNTREND' else '→'
        }
    
    def _calculate_trend(self, history: List[Dict]) -> Dict:
        """Calculate trend from history"""
        if len(history) < 3:
            return {'trend': 'NEUTRAL', 'velocity': 0, 'context': 'NEUTRAL', 'strength': 0}
        
        midpoints = [day['va_midpoint'] for day in history]
        
        # Simple velocity: End - Start
        velocity_pct = ((midpoints[-1] - midpoints[0]) / midpoints[0]) * 100
        
        if velocity_pct > 1.0:
            trend = 'UPTREND'
            context = 'BULLISH'
        elif velocity_pct < -1.0:
            trend = 'DOWNTREND'
            context = 'BEARISH'
        else:
            trend = 'SIDEWAYS'
            context = 'NEUTRAL'
            
        return {
            'trend': trend,
            'velocity': velocity_pct / len(history), # Avg daily change
            'context': context,
            'strength': min(100, abs(velocity_pct) * 10)
        }


class POCZoneCalculator:
    """Calculate POC zones instead of single lines"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
    
    def calculate_poc_zone(self, poc_price: float, zone_width_pct: float = 0.5) -> Dict:
        width = poc_price * (zone_width_pct / 100)
        return {
            'poc': poc_price,
            'zone_upper': poc_price + (width / 2),
            'zone_lower': poc_price - (width / 2),
            'zone_width_dollars': width
        }
    
    def multi_timeframe_poc(self) -> Dict:
        """
        Get POC from multiple timeframes
        """
        # Simplified for responsiveness: Just checking Daily + Weekly
        timeframes = {
            'intraday': {'period': '1d', 'interval': '5m'},
            'daily': {'period': '5d', 'interval': '1h'},
            'weekly': {'period': '1mo', 'interval': '1d'}
        }
        
        result = {}
        poc_list = []
        
        for tf_name, params in timeframes.items():
            eng = VolumeProfileEngine(self.ticker, period=params['period'], interval=params['interval'])
            m = eng.get_all_metrics()
            if m['poc'] > 0:
                result[tf_name] = self.calculate_poc_zone(m['poc'])
                poc_list.append(m['poc'])
            else:
                result[tf_name] = None
                
        # Confluence
        confluence = []
        if len(poc_list) >= 2:
            poc_list.sort()
            for i in range(len(poc_list)-1):
                p1 = poc_list[i]
                p2 = poc_list[i+1]
                if abs((p1-p2)/p1) < 0.005: # 0.5%
                    confluence.append({
                        'price': (p1+p2)/2,
                        'strength': 100,
                        'timeframes': 2,
                        'zone': self.calculate_poc_zone((p1+p2)/2, 0.8)
                    })
                    
        return {
            **result,
            'confluence': confluence,
            'confluence_strength': len(confluence) * 50
        }

# Helpers
def analyze_ticker(ticker: str) -> Dict:
    eng = VolumeProfileEngine(ticker)
    return eng.get_all_metrics()

def get_key_levels(ticker: str) -> Dict:
    eng = VolumeProfileEngine(ticker)
    return eng.get_all_metrics()
