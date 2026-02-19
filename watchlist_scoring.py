import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

class WatchlistScorer:
    """
    Ranks watchlist tickers based on a multi-factor composite score.
    Factors:
    - Technical (40%): RSI, Moving Average Alignment, Relative Strength
    - Fundamental (40%): P/E Ratio, Market Cap, Revenue Growth (Mock/Simple)
    - Quantitative (20%): Volatility, Beta
    """
    
    def __init__(self):
        pass

    def fetch_data(self, tickers: List[str]) -> pd.DataFrame:
        """Fetch necessary data for all tickers."""
        data = []
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="6mo")
                info = t.info
                
                if hist.empty:
                    continue
                
                # --- Technicals ---
                close = hist['Close']
                # RSI
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                # SMA Alignment
                sma50 = close.rolling(window=50).mean().iloc[-1]
                sma200 = close.rolling(window=200).mean().iloc[-1] if len(close) > 200 else sma50
                trend = 1 if close.iloc[-1] > sma50 > sma200 else 0.5 if close.iloc[-1] > sma50 else 0
                
                # Relative Performance (vs starting price 6mo ago)
                perf_6m = (close.iloc[-1] - close.iloc[0]) / close.iloc[0]
                
                # --- Fundamentals ---
                pe = info.get('trailingPE', 25) # Default to market avg if missing
                mkt_cap = info.get('marketCap', 1e9)
                
                # --- Quant ---
                # Volatility (Annualized)
                vol = close.pct_change().std() * np.sqrt(252)
                beta = info.get('beta', 1.0)
                
                data.append({
                    'Ticker': ticker,
                    'Price': close.iloc[-1],
                    'RSI': rsi,
                    'Trend_Score': trend, # 0 to 1
                    'Perf_6m': perf_6m,
                    'PE_Ratio': pe if pe is not None else 25,
                    'Market_Cap': mkt_cap,
                    'Volatility': vol,
                    'Beta': beta if beta is not None else 1.0
                })
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                
        return pd.DataFrame(data)

    def calculate_scores(self, df: pd.DataFrame, 
                         w_tech: float = 0.4, 
                         w_fund: float = 0.4, 
                         w_quant: float = 0.2) -> pd.DataFrame:
        """Calculate composite scores based on normalized metrics."""
        if df.empty:
            return df
            
        scored = df.copy()
        
        # --- Normalization (0-100 scale) ---
        
        # Technical Score
        # RSI: Best near 50-70? Or just momentum? Let's say higher is better for momentum, but punish > 80?
        # Simple: Higher RSI (up to 70) is better.
        scored['Norm_RSI'] = scored['RSI'].clip(0, 100)
        scored['Norm_Trend'] = scored['Trend_Score'] * 100
        # Relative Perf: Rank percentile
        scored['Norm_Perf'] = scored['Perf_6m'].rank(pct=True) * 100
        
        scored['Tech_Composite'] = (scored['Norm_RSI'] * 0.3 + 
                                   scored['Norm_Trend'] * 0.4 + 
                                   scored['Norm_Perf'] * 0.3)
        
        # Fundamental Score
        # P/E: Lower is better (value), but not negative.
        # Invert P/E for scoring: 1/PE * constant
        # For simplicity, rank percentile of inverted PE
        scored['Inv_PE'] = 1 / scored['PE_Ratio'].replace(0, 1) # Avoid div/0
        scored['Norm_Value'] = scored['Inv_PE'].rank(pct=True) * 100
        scored['Norm_Size'] = scored['Market_Cap'].rank(pct=True) * 100 # Bigger is "safer"/better for this metric
        
        scored['Fund_Composite'] = (scored['Norm_Value'] * 0.6 + 
                                   scored['Norm_Size'] * 0.4)
                                   
        # Quant Score
        # Volatility: Lower is better? Or higher? Depends. Let's say lower vol is "better" (safer).
        scored['Nav_Vol'] = (1 / scored['Volatility']).rank(pct=True) * 100
        # Beta: Closer to 1 is neutral? Let's just use Volatility for simplicity.
        scored['Quant_Composite'] = scored['Nav_Vol']
        
        # --- Final Weighted Score ---
        scored['Total_Score'] = (scored['Tech_Composite'] * w_tech + 
                                scored['Fund_Composite'] * w_fund + 
                                scored['Quant_Composite'] * w_quant)
                                
        scored['Total_Score'] = scored['Total_Score'].round(1)
        
        return scored.sort_values('Total_Score', ascending=False)
