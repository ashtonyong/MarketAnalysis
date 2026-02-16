"""
Options Flow Analysis
Displays options chain, put/call ratio, max pain, and unusual volume.
Uses yfinance options data - 100% FREE.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime


class OptionsFlowAnalyzer:
    """Analyze options chain data for a ticker."""

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)

    def get_expirations(self):
        """Get available expiration dates."""
        try:
            return list(self.stock.options)
        except Exception:
            return []

    def analyze(self, expiration: Optional[str] = None) -> Dict:
        """Full options analysis for a given expiration."""
        expirations = self.get_expirations()
        if not expirations:
            return {'error': 'No options data available for this ticker'}

        if expiration is None:
            expiration = expirations[0]  # Nearest

        try:
            chain = self.stock.option_chain(expiration)
            calls = chain.calls
            puts = chain.puts
        except Exception as e:
            return {'error': str(e)}

        # Current price
        try:
            hist = self.stock.history(period='1d')
            current_price = float(hist['Close'].iloc[-1]) if not hist.empty else 0
        except Exception:
            current_price = 0

        # Put/Call Ratio
        call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
        put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
        pc_ratio = put_volume / call_volume if call_volume > 0 else 0

        call_oi = calls['openInterest'].sum() if 'openInterest' in calls.columns else 0
        put_oi = puts['openInterest'].sum() if 'openInterest' in puts.columns else 0
        pc_oi_ratio = put_oi / call_oi if call_oi > 0 else 0

        # Max Pain
        max_pain = self._calculate_max_pain(calls, puts)

        # Unusual Volume
        unusual_calls = self._find_unusual_volume(calls, 'CALL')
        unusual_puts = self._find_unusual_volume(puts, 'PUT')
        unusual = pd.concat([unusual_calls, unusual_puts]).sort_values(
            'volume', ascending=False
        ).head(10) if not unusual_calls.empty or not unusual_puts.empty else pd.DataFrame()

        # Summary stats
        call_iv_mean = calls['impliedVolatility'].mean() * 100 if 'impliedVolatility' in calls.columns else 0
        put_iv_mean = puts['impliedVolatility'].mean() * 100 if 'impliedVolatility' in puts.columns else 0

        # Sentiment from options
        if pc_ratio < 0.7:
            sentiment = 'BULLISH (low put/call)'
        elif pc_ratio > 1.3:
            sentiment = 'BEARISH (high put/call)'
        else:
            sentiment = 'NEUTRAL'

        return {
            'expiration': expiration,
            'current_price': current_price,
            'calls': calls,
            'puts': puts,
            'call_volume': int(call_volume) if not pd.isna(call_volume) else 0,
            'put_volume': int(put_volume) if not pd.isna(put_volume) else 0,
            'pc_ratio': round(pc_ratio, 2) if not pd.isna(pc_ratio) else 0,
            'call_oi': int(call_oi) if not pd.isna(call_oi) else 0,
            'put_oi': int(put_oi) if not pd.isna(put_oi) else 0,
            'pc_oi_ratio': round(pc_oi_ratio, 2) if not pd.isna(pc_oi_ratio) else 0,
            'max_pain': max_pain,
            'unusual_activity': unusual,
            'call_iv': round(call_iv_mean, 1),
            'put_iv': round(put_iv_mean, 1),
            'sentiment': sentiment,
        }

    def _calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> float:
        """
        Calculate max pain price.
        Max pain = the strike price where option sellers lose the least money.
        """
        if calls.empty and puts.empty:
            return 0

        strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
        if not strikes:
            return 0

        min_pain = float('inf')
        max_pain_strike = strikes[0]

        for strike in strikes:
            # Call pain: all calls with strike < current strike are ITM
            call_pain = 0
            for _, row in calls.iterrows():
                if strike > row['strike']:
                    oi = row.get('openInterest', 0)
                    if pd.notna(oi):
                        call_pain += (strike - row['strike']) * oi

            # Put pain: all puts with strike > current strike are ITM
            put_pain = 0
            for _, row in puts.iterrows():
                if strike < row['strike']:
                    oi = row.get('openInterest', 0)
                    if pd.notna(oi):
                        put_pain += (row['strike'] - strike) * oi

            total_pain = call_pain + put_pain
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = strike

        return float(max_pain_strike)

    def _find_unusual_volume(self, chain: pd.DataFrame, option_type: str) -> pd.DataFrame:
        """Find options with unusually high volume relative to open interest."""
        if chain.empty or 'volume' not in chain.columns:
            return pd.DataFrame()

        df = chain.copy()
        df['type'] = option_type
        df = df[df['volume'] > 0]

        if df.empty:
            return pd.DataFrame()

        vol_mean = df['volume'].mean()
        vol_std = df['volume'].std()
        threshold = vol_mean + 1.5 * vol_std

        unusual = df[df['volume'] >= threshold].copy()
        if unusual.empty:
            return pd.DataFrame()

        unusual['vol_oi_ratio'] = np.where(
            unusual['openInterest'] > 0,
            (unusual['volume'] / unusual['openInterest']).round(1),
            0
        )

        return unusual[['type', 'strike', 'volume', 'openInterest',
                        'vol_oi_ratio', 'impliedVolatility', 'lastPrice']].copy()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    ofa = OptionsFlowAnalyzer('SPY')
    result = ofa.analyze()
    if 'error' not in result:
        print(f"Expiration: {result['expiration']}")
        print(f"P/C Ratio: {result['pc_ratio']} ({result['sentiment']})")
        print(f"Max Pain: ${result['max_pain']:.2f}")
        print(f"Call Vol: {result['call_volume']:,} | Put Vol: {result['put_volume']:,}")
        print(f"Call IV: {result['call_iv']}% | Put IV: {result['put_iv']}%")
    else:
        print(result['error'])
