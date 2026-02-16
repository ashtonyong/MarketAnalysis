"""
Market Profile Engine (TPO)
Logic for time-based profile analysis (Letters A-Z).
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import yfinance as yf
from collections import defaultdict

class MarketProfileEngine:
    """
    Market Profile (TPO - Time Price Opportunity) Calculator
    Different from Volume Profile - uses TIME not VOLUME
    """
    
    def __init__(self, ticker: str = None, data: pd.DataFrame = None):
        self.ticker = ticker
        self.data = data
        self.tpo_profile = None
        self.letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        
    def fetch_intraday_data(self) -> pd.DataFrame:
        """Fetch intraday data for TPO calculation if not provided"""
        if self.data is not None and not self.data.empty:
            return self.data
            
        if not self.ticker:
            raise ValueError("Ticker required if data not provided")
            
        stock = yf.Ticker(self.ticker)
        # Get today's data in 30-min intervals
        # Note: yfinance '1d' period with '30m' interval gets recent day
        data = stock.history(period='5d', interval='30m') 
        
        if data.empty:
            raise ValueError(f"No data for {self.ticker}")
        
        # Filter for just the last day
        last_date = data.index[-1].date()
        self.data = data[data.index.date == last_date].copy()
        return self.data
    
    def calculate_tpo_profile(self, period_minutes: int = 30) -> Dict:
        """
        Calculate TPO (Time Price Opportunity) profile
        """
        data = self.fetch_intraday_data()
        
        if data.empty: return {}

        # Determine price bins
        price_min = data['Low'].min()
        price_max = data['High'].max()
        tick_size = self._calculate_tick_size(price_min, price_max)
        
        # Create price levels
        # We use a dictionary mapping price_level -> list of letters
        tpo_data = defaultdict(list)
        
        # Assign letters to each period
        # Resample if needed to ensure 30m periods logic matches letters
        # Assuming data is already 30m or close to it.
        
        for idx, (timestamp, row) in enumerate(data.iterrows()):
            if idx >= len(self.letters):
                break 
            
            letter = self.letters[idx]
            high = row['High']
            low = row['Low']
            
            # Align high/low to ticks
            high_tick = int(high / tick_size)
            low_tick = int(low / tick_size)
            
            # Mark all price levels touched in this period
            for tick in range(low_tick, high_tick + 1):
                price = tick * tick_size
                tpo_data[price].append(letter)
        
        # Convert to structured list
        profile = []
        # Sort by price descending
        sorted_prices = sorted(tpo_data.keys(), reverse=True)
        
        for price in sorted_prices:
            letters_list = tpo_data[price]
            profile.append({
                'price': price,
                'letters': letters_list,
                'tpo_count': len(letters_list),
                'letter_string': ''.join(sorted(letters_list)) # Sort letters for display (A, B, C...)
            })
        
        # Store as DataFrame for internal analysis
        self.tpo_profile = pd.DataFrame(profile)
        
        # Calculate derived metrics
        ib = self.find_initial_balance()
        extensions = self.detect_range_extensions()
        shape = self.classify_profile_shape()
        
        return {
            'profile': profile,
            'initial_balance': ib,
            'extensions': extensions,
            'shape': shape,
            'day_type': extensions.get('day_type', 'Unknown'),
            'tick_size': tick_size
        }
    
    def _calculate_tick_size(self, price_min: float, price_max: float) -> float:
        """Calculate appropriate tick size for TPO display"""
        price_range = price_max - price_min
        if price_range == 0: return 0.01
        
        target_levels = 50
        raw_tick = price_range / target_levels
        
        # Round to common tick sizes
        if raw_tick < 0.01: return 0.01
        if raw_tick < 0.05: return 0.05
        if raw_tick < 0.10: return 0.10
        if raw_tick < 0.25: return 0.25
        if raw_tick < 0.50: return 0.50
        if raw_tick < 1.0: return 1.0
        return round(raw_tick)
    
    def find_initial_balance(self) -> Dict:
        """
        Initial Balance (IB) = Range of first hour (periods A + B)
        """
        if self.tpo_profile is None or self.tpo_profile.empty:
            return {'high': 0, 'low': 0, 'range': 0}
        
        # Filter rows where letters contain 'A' or 'B'
        # Since 'letters' is a list, we check if set intersection is non-empty
        ib_mask = self.tpo_profile['letters'].apply(lambda x: any(l in ['A', 'B'] for l in x))
        ib_rows = self.tpo_profile[ib_mask]
        
        if ib_rows.empty:
            return {'high': 0, 'low': 0, 'range': 0}
            
        ib_high = ib_rows['price'].max()
        ib_low = ib_rows['price'].min()
        
        return {
            'high': ib_high,
            'low': ib_low,
            'range': ib_high - ib_low,
            'midpoint': (ib_high + ib_low) / 2
        }
    
    def detect_range_extensions(self) -> Dict:
        """
        Detect if price extended beyond Initial Balance
        """
        ib = self.find_initial_balance()
        if ib['range'] == 0: return {'day_type': 'Unknown'}
        
        # Check letters after B (C onwards)
        # Assuming standard letters string
        extension_letters = self.letters[2:] 
        
        ext_up = []
        ext_down = []
        
        # Filter for rows containing extension letters
        # Optimize: Iterate through profile once? Or filter dataframe?
        # Let's check min/max price of each letter C+
        
        # Iterate through profile to find max/min price for each letter
        # This is heavy if many letters, but usually just ~13 (A-M)
        
        for letter in extension_letters:
            # Check if this letter exists in profile
            # Only strictly necessary to check letters that actually appeared
            pass 

        # Faster approach: Look at High/Low of periods C+ from source data? 
        # But we want TPO levels.
        # Let's use the TPO profile.
        
        ext_up_found = False
        ext_down_found = False
        
        # Prices > IB High
        above_ib = self.tpo_profile[self.tpo_profile['price'] > ib['high']]
        # Check if any letters C+ are in there
        for _, row in above_ib.iterrows():
            if any(l in extension_letters for l in row['letters']):
                ext_up_found = True
                break
                
        # Prices < IB Low
        below_ib = self.tpo_profile[self.tpo_profile['price'] < ib['low']]
        for _, row in below_ib.iterrows():
            if any(l in extension_letters for l in row['letters']):
                ext_down_found = True
                break
        
        # Classification
        if ext_up_found and ext_down_found:
            day_type = 'NEUTRAL_DAY' # Range expansion both sides
        elif ext_up_found:
            day_type = 'TREND_UP'
        elif ext_down_found:
            day_type = 'TREND_DOWN'
        else:
            day_type = 'NORMAL_DAY' # Stayed within IB (mostly) or no significant extension
            
        return {
            'extended_up': ext_up_found,
            'extended_down': ext_down_found,
            'day_type': day_type
        }
    
    def classify_profile_shape(self) -> Dict:
        """
        Classify Market Profile shape: P, b, D, Normal
        """
        if self.tpo_profile is None or self.tpo_profile.empty:
            return {'shape': 'Unknown'}
            
        # Get count array
        # Sort by price ascending for shape analysis (bottom to top)
        df_sorted = self.tpo_profile.sort_values('price', ascending=True)
        counts = df_sorted['tpo_count'].values
        prices = df_sorted['price'].values
        
        if len(counts) == 0: return {'shape': 'Unknown'}

        max_tpo = counts.max()
        # Indices where count is high (> 80% of max)
        peak_indices = np.where(counts >= max_tpo * 0.8)[0]
        
        if len(peak_indices) == 0: return {'shape': 'Unknown'}

        # Calculate center of mass of peaks (relative position 0..1)
        # 0 = Bottom, 1 = Top
        avg_peak_idx = np.mean(peak_indices)
        rel_pos = avg_peak_idx / len(counts)
        
        # Double Distribution check
        # Check for two separated peaks with a valley in between
        # (Simplified logic)
        is_double = False
        if len(peak_indices) >= 2:
            # Check if peaks are far apart
            if (peak_indices[-1] - peak_indices[0]) > (len(counts) * 0.4):
                # Check for valley
                mid = int((peak_indices[-1] + peak_indices[0]) / 2)
                if counts[mid] < max_tpo * 0.6:
                    is_double = True
                    
        if is_double:
            shape = 'D'
            desc = 'Double Distribution'
        elif rel_pos > 0.65:
            shape = 'P'
            desc = 'Short Covering / Trend Up'
        elif rel_pos < 0.35:
            shape = 'b'
            desc = 'Long Liquidation / Trend Down'
        else:
            shape = 'Normal'
            desc = 'Balanced / Bell Curve'
            
        return {
            'shape': shape,
            'description': desc,
            'confidence': 80 # Static for now
        }
