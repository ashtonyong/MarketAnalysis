"""
Profile Statistics
Calculates efficiency, bias, and distribution metrics.
"""
from typing import Dict
import pandas as pd
import numpy as np

class ProfileStatistics:
    """
    Deep dive metrics.
    """
    
    def __init__(self, profile_df: pd.DataFrame, price_data: pd.DataFrame, 
                 poc: float, vah: float, val: float):
        self.profile = profile_df
        # Normalize
        if 'Volume' in self.profile.columns:
            self.profile = self.profile.rename(columns={'Volume': 'volume', 'Price': 'price'})
            
        self.data = price_data
        self.poc = poc
        self.vah = vah
        self.val = val
        
    def calculate_all_statistics(self) -> Dict:
        return {
            'profile_width': self.calculate_profile_width(),
            'volume_distribution': self.calculate_volume_distribution(),
            'time_in_va': self.calculate_time_in_va(),
            'profile_efficiency': self.calculate_profile_efficiency(),
            'trend_indicators': self.calculate_trend_indicators()
        }

    def calculate_profile_width(self):
        rng = self.vah - self.val
        mid = (self.vah + self.val) / 2
        pct = (rng / mid) * 100 if mid else 0
        return {
            'range_dollars': rng,
            'range_pct': pct,
            'volatility': 'HIGH' if pct > 1.5 else 'LOW',
            'interpretation': f"Range is {pct:.2f}% of price"
        }

    def calculate_volume_distribution(self):
        above = self.profile[self.profile['price'] > self.poc]['volume'].sum()
        below = self.profile[self.profile['price'] < self.poc]['volume'].sum()
        total = above + below
        if total == 0: return {}
        
        above_r = (above / total) * 100
        bias = 'BULLISH' if above_r > 55 else 'BEARISH' if above_r < 45 else 'BALANCED'
        
        return {
            'above_ratio': above_r,
            'below_ratio': 100 - above_r,
            'bias': bias,
            'interpretation': f"{bias} Bias ({above_r:.1f}% volume above POC)"
        }

    def calculate_time_in_va(self):
        if self.data is None or self.data.empty: return {}
        
        inside = self.data[
            (self.data['Close'] >= self.val) & (self.data['Close'] <= self.vah)
        ]
        pct = (len(inside) / len(self.data)) * 100
        
        return {
            'pct_inside_va': pct,
            'interpretation': f"Spent {pct:.1f}% time in Value Area"
        }

    def calculate_profile_efficiency(self):
        # Trending (High Eff) vs Ranging (Low Eff)
        # Simple proxy: (Close - Open) / Profile Range
        if self.data is None or self.data.empty: return {}
        
        move = abs(self.data['Close'].iloc[-1] - self.data['Open'].iloc[0])
        prof_range = self.profile['price'].max() - self.profile['price'].min()
        
        eff = (move / prof_range * 100) if prof_range else 0
        
        return {
            'efficiency_pct': eff,
            'profile_type': 'TRENDING' if eff > 50 else 'BALANCED',
            'interpretation': f"Efficiency: {eff:.1f}%"
        }

    def calculate_trend_indicators(self):
        if self.data is None or self.data.empty: return {}
        curr = self.data['Close'].iloc[-1]
        
        relation = "AT_POC"
        if curr > self.poc: relation = "ABOVE_POC"
        if curr < self.poc: relation = "BELOW_POC"
        
        return {
            'trend': 'UP' if relation == 'ABOVE_POC' else 'DOWN',
            'price_vs_poc_pct': ((curr - self.poc)/self.poc)*100,
            'interpretation': f"Price is {relation}"
        }
