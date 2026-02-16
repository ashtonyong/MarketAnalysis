"""
Composite Profile Builder
Merges multiple daily profiles into a single long-term profile.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from volume_profile_engine import VolumeProfileEngine

class CompositeProfileBuilder:
    """
    Builds Composite Profiles (5d, 10d, Weekly, Monthly etc.)
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        
    def build_composite(self, days: int = 5, weighting: str = 'equal') -> Dict:
        """
        Merges last N days of data into one composite volume profile.
        weighting: 'equal', 'linear', or 'exponential'
        """
        # Fetch data for N days (using 1h interval for efficiency in composites)
        # Getting slightly more data to be safe
        period = "1mo" if days > 20 else f"{days+5}d"
        engine = VolumeProfileEngine(self.ticker, period=period, interval="1h")
        engine.fetch_data()
        
        if engine.data.empty: return {}
        
        # Split into Daily Buckets
        daily_groups = []
        # Group by Date
        for date, group in engine.data.groupby(engine.data.index.date):
            if not group.empty:
                daily_groups.append(group)
        
        # Take the last N days
        daily_groups = daily_groups[-days:]
        if not daily_groups: return {}
        
        actual_days = len(daily_groups)
        weights = self._calculate_weights(actual_days, weighting)
        
        # Combine Volume with Weights
        # We need a unified price grid. 
        # Find global min/max price
        all_lows = [g['Low'].min() for g in daily_groups]
        all_highs = [g['High'].max() for g in daily_groups]
        min_p = min(all_lows)
        max_p = max(all_highs)
        
        # 100 bins for composite
        bins = np.linspace(min_p, max_p, 101)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        comp_vol = np.zeros(len(bin_centers))
        
        for idx, day_df in enumerate(daily_groups):
            w = weights[idx]
            # Calculate daily profile (histogram)
            if day_df.empty: continue
            
            # Use same bins
            vol_hist, _ = np.histogram(day_df['Close'], bins=bins, weights=day_df['Volume'])
            
            # Add weighted volume
            comp_vol += (vol_hist * w)
            
        # Create DataFrame
        comp_profile = pd.DataFrame({'Price': bin_centers, 'Volume': comp_vol})
        comp_profile = comp_profile[comp_profile['Volume'] > 0]
        
        # Calculate Levels on Composite
        # Use Engine helper methods temporarily or implementing simplified version here
        poc_idx = comp_profile['Volume'].idxmax()
        poc = comp_profile.loc[poc_idx, 'Price']
        
        # VA Calculation
        total_vol = comp_profile['Volume'].sum()
        target = total_vol * 0.70
        sorted_prof = comp_profile.sort_values('Volume', ascending=False)
        cum_vol = 0
        in_va_prices = []
        for _, row in sorted_prof.iterrows():
            cum_vol += row['Volume']
            in_va_prices.append(row['Price'])
            if cum_vol >= target: break
            
        vah = max(in_va_prices) if in_va_prices else poc
        val = min(in_va_prices) if in_va_prices else poc
        
        return {
            'days': actual_days,
            'profile': comp_profile.to_dict('records'),
            'poc': poc,
            'vah': vah,
            'val': val,
            'weighting': weighting,
            'volume_total': total_vol,
            'date_range': {
                'start': daily_groups[0].index[0].strftime('%Y-%m-%d'),
                'end': daily_groups[-1].index[-1].strftime('%Y-%m-%d')
            }
        }
        
    def _calculate_weights(self, n: int, method: str) -> np.ndarray:
        if method == 'linear':
            # 1, 2, 3 ... N
            return np.arange(1, n + 1)
        elif method == 'exponential':
            # 1.5^0, 1.5^1 ...
            return np.power(1.5, np.arange(n))
        else:
            # Equal
            return np.ones(n)
            
    def compare_composites(self, days_list: List[int] = [5, 10, 20]) -> Dict:
        """
        Compare POCs across multiple composite timeframes.
        """
        results = {}
        pocs = []
        
        for d in days_list:
            comp = self.build_composite(d, weighting='exponential')
            if comp:
                results[f'{d}d'] = comp
                pocs.append({'days': d, 'poc': comp['poc']})
                
        # Find Confluence
        confluence = []
        if len(pocs) >= 2:
            # Sort by POC price
            pocs.sort(key=lambda x: x['poc'])
            
            # Check neighbors
            for i in range(len(pocs)-1):
                p1 = pocs[i]
                p2 = pocs[i+1]
                
                # Check % diff
                diff = abs(p1['poc'] - p2['poc']) / p1['poc']
                if diff < 0.005: # 0.5% tolerance
                    confluence.append({
                        'price': (p1['poc'] + p2['poc']) / 2,
                        'timeframes': [p1['days'], p2['days']],
                        'strength': 80 # Arbitrary high strength for multi-tf match
                    })
                    
        return {
            'composites': results, # Summary data
            'confluence': confluence
        }
