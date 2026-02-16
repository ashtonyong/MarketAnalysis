"""
Correlation Analysis Engine
Computes correlation matrix between multiple tickers.
Helps spot divergences and inter-market relationships.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict


class CorrelationAnalyzer:
    """Analyze correlations between multiple tickers."""

    DEFAULT_PAIRS = {
        'Indices': ['SPY', 'QQQ', 'DIA', 'IWM'],
        'Macro': ['SPY', 'GC=F', 'TLT', 'DX-Y.NYB'],
        'Tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META'],
        'Crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD'],
    }

    def __init__(self, tickers: List[str], period: str = '3mo'):
        self.tickers = tickers
        self.period = period
        self.data = None

    def fetch_data(self) -> pd.DataFrame:
        """Fetch close prices for all tickers."""
        closes = {}
        for t in self.tickers:
            try:
                df = yf.download(t, period=self.period, interval='1d',
                                 progress=False, auto_adjust=True)
                if df is not None and not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    closes[t] = df['Close']
            except Exception:
                pass

        self.data = pd.DataFrame(closes).dropna()
        return self.data

    def compute_correlation(self) -> pd.DataFrame:
        """Compute correlation matrix of daily returns."""
        if self.data is None or self.data.empty:
            self.fetch_data()
        returns = self.data.pct_change().dropna()
        return returns.corr().round(3)

    def compute_rolling_correlation(self, ticker1: str, ticker2: str,
                                     window: int = 20) -> pd.Series:
        """Compute rolling correlation between two tickers."""
        if self.data is None:
            self.fetch_data()
        returns = self.data.pct_change().dropna()
        if ticker1 in returns.columns and ticker2 in returns.columns:
            return returns[ticker1].rolling(window).corr(returns[ticker2])
        return pd.Series()

    def get_summary(self) -> Dict:
        """Get a summary of strongest/weakest correlations."""
        corr = self.compute_correlation()
        pairs = []
        cols = corr.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                pairs.append({
                    'pair': f"{cols[i]} / {cols[j]}",
                    'correlation': corr.iloc[i, j],
                })
        pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

        return {
            'correlation_matrix': corr,
            'strongest_positive': [p for p in pairs if p['correlation'] > 0][:5],
            'strongest_negative': [p for p in pairs if p['correlation'] < 0][:5],
            'all_pairs': pairs,
        }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    ca = CorrelationAnalyzer(['SPY', 'QQQ', 'GC=F', 'TLT'])
    summary = ca.get_summary()
    print("Correlation Matrix:")
    print(summary['correlation_matrix'])
    print("\nStrongest Positive:")
    for p in summary['strongest_positive']:
        print(f"  {p['pair']}: {p['correlation']:.3f}")
    print("\nStrongest Negative:")
    for p in summary['strongest_negative']:
        print(f"  {p['pair']}: {p['correlation']:.3f}")
