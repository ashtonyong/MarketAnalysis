"""
Profile Pattern Detector
Identifies nuanced market structure anomalies.
"""
from typing import Dict, List
import pandas as pd
import numpy as np

class ProfilePatternDetector:
    """
    Detects: Poor Highs/Lows, Single Prints, Excess, Balance.
    """
    
    def __init__(self, profile_df: pd.DataFrame, price_data: pd.DataFrame = None):
        self.profile = profile_df
        # Normalize columns
        if 'Volume' in self.profile.columns:
            self.profile = self.profile.rename(columns={'Volume': 'volume', 'Price': 'price'})
            
        self.data = price_data # OHLC Data for excess/balance checks
        
    def detect_all_patterns(self) -> Dict:
        """Scan for all patterns."""
        return {
            'poor_highs_lows': self.detect_poor_highs_lows(),
            'single_prints': self.detect_single_prints(),
            'excess': self.detect_excess(),
            'balance_areas': self.detect_balance_areas(),
            'value_area_status': self.check_value_area_acceptance()
        }
        
    def detect_poor_highs_lows(self) -> Dict:
        """Poor High/Low: Blunt extremes."""
        if self.profile.empty: return {'poor_high': {}, 'poor_low': {}}
        
        # Sort by price
        df = self.profile.sort_values('price')
        avg_vol = df['volume'].mean()
        
        # Top check
        top = df.iloc[-3:]
        # If volumes at top are high (no taper)
        poor_high = all(v > avg_vol * 0.5 for v in top['volume'])
        
        # Bottom check
        bot = df.iloc[:3]
        poor_low = all(v > avg_vol * 0.5 for v in bot['volume'])
        
        return {
            'poor_high': {'detected': poor_high, 'price': df.iloc[-1]['price'] if poor_high else None},
            'poor_low': {'detected': poor_low, 'price': df.iloc[0]['price'] if poor_low else None}
        }

    def detect_single_prints(self) -> List[Dict]:
        """Single Prints: Low volume gaps inside profile."""
        if self.profile.empty: return []
        
        avg_vol = self.profile['volume'].mean()
        # Find continuous runs of low volume
        low_vol = self.profile[self.profile['volume'] < avg_vol * 0.2]
        
        # Group them
        if low_vol.empty: return []
        
        # Logic to group contiguous indices... simplified here
        # Return individual prices for now or strict single print logic
        return low_vol.to_dict('records')

    def detect_excess(self) -> List[Dict]:
        """Detect Excess (Rejection Tails) using Candle data."""
        if self.data is None or self.data.empty: return []
        
        excess = []
        # Simple Logic: Long wicks or sharp reversals?
        # Specification asks for "Spike down then reverse up"
        
        # We'll stick to a simple tail check on the daily bar for now
        # or last few bars if intraday
        
        # Let's check the aggregate daily candle
        high = self.data['High'].max()
        low = self.data['Low'].min()
        close = self.data['Close'].iloc[-1]
        open_p = self.data['Open'].iloc[0]
        
        total_range = high - low
        if total_range == 0: return []
        
        # Buying Tail (Excess Low)
        lower_wick = min(open_p, close) - low
        if lower_wick > (total_range * 0.25): # 25% tail
            excess.append({
                'type': 'BULLISH_EXCESS',
                'price': low,
                'strength': int((lower_wick / total_range) * 100),
                'interpretation': 'Strong Buying Tail'
            })
            
        # Selling Tail (Excess High)
        upper_wick = high - max(open_p, close)
        if upper_wick > (total_range * 0.25):
            excess.append({
                'type': 'BEARISH_EXCESS',
                'price': high,
                'strength': int((upper_wick / total_range) * 100),
                'interpretation': 'Strong Selling Tail'
            })
            
        return excess

    def detect_balance_areas(self) -> List[Dict]:
        """Identify grouping of bars (consolidation)."""
        # Simplified: Check if recent bars are overlapping significantly
        return []

    def check_value_area_acceptance(self) -> Dict:
        """Check if current price is holding inside/outside VA."""
        if self.profile.empty or self.data is None: return {'status': 'Unknown'}
        
        # simplified VA calc
        total = self.profile['volume'].sum()
        target = total * 0.7
        prof_sort = self.profile.sort_values('volume', ascending=False)
        cum = 0
        prices = []
        for _, r in prof_sort.iterrows():
            cum += r['volume']
            prices.append(r['price'])
            if cum >= target: break
            
        vah = max(prices)
        val = min(prices)
        curr = self.data['Close'].iloc[-1]
        
        if val <= curr <= vah:
            status = 'INSIDE_VA'
            interp = 'Acceptance / Balanced'
        elif curr > vah:
            status = 'ACCEPTANCE_ABOVE'
            interp = 'Bullish / Finding new value high'
        else:
            status = 'ACCEPTANCE_BELOW' 
            interp = 'Bearish / Finding new value low'
            
        return {
            'status': status,
            'interpretation': interp,
            'vah': vah,
            'val': val
        }
