
import numpy as np
import pandas as pd
from scipy import stats
from datetime import timedelta

class MonteCarloSimulator:
    def __init__(self, trades_df, initial_capital=10000, simulations=5000):
        self.trades_df = trades_df
        self.capital = initial_capital
        self.simulations = simulations

    def run(self):
        if self.trades_df.empty:
            return {}
        
        pnl_series = self.trades_df['P&L'].values
        results = []
        
        for _ in range(self.simulations):
            # Shuffle trades with replacement/bootstrap
            sim_pnl = np.random.choice(pnl_series, size=len(pnl_series), replace=True)
            total_pnl = np.sum(sim_pnl)
            final_equity = self.capital + total_pnl
            results.append(final_equity)
            
        results = np.array(results)
        return {
            "median": np.median(results),
            "best_case": np.percentile(results, 95),
            "worst_case": np.percentile(results, 5),
            "prob_profit": np.mean(results > self.capital) * 100,
            "simulations": results.tolist() 
        }

class KellyCriterion:
    def calculate(self, win_rate, win_loss_ratio):
        """
        Kelly = W - ((1 - W) / R)
        Where W = Win probability, R = Win/Loss ratio
        """
        if win_loss_ratio <= 0: return 0
        kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)
        return max(0, kelly_pct) # No negative sizing

class RegimeDetector:
    def detect(self, df):
        """
        Simple regime detection using ADX and ATR structure.
        Uses 'pandas_ta' if available, otherwise manual calculation.
        """
        # Placeholder logic without external lib dependency for now to ensure robustness
        # Calculation of ADX manually or use simple volatility/trend check
        
        # Simple Logic: 
        # Trending: SMA 20 > SMA 50 and Price > SMA 20
        # Ranging: ADX < 20 (Simulated here with standard deviation check)
        
        window = 20
        df['SMA_20'] = df['Close'].rolling(window).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['StdDev'] = df['Close'].rolling(window).std()
        
        last = df.iloc[-1]
        
        regime = "NORMAL"
        if last['SMA_20'] > last['SMA_50']:
            regime = "TRENDING UP"
        elif last['SMA_20'] < last['SMA_50']:
            regime = "TRENDING DOWN"
            
        # Volatility check
        if last['StdDev'] > df['StdDev'].mean() * 1.5:
            regime = "VOLATILE"
            
        return regime

class ZScoreCalculator:
    def calculate(self, series, window=20):
        mean = series.rolling(window).mean()
        std = series.rolling(window).std()
        z = (series - mean) / std
        return z.iloc[-1]

class SetupScorer:
    def score(self, profile_data, current_price, regime):
        # 0-100 score based on confluence
        score = 50
        
        # Value Area Confluence
        if profile_data['val'] < current_price < profile_data['vah']:
            score += 10 # Inside value implies rotation/mean reversion
        else:
            score += 20 # Outside value implies breakout potential or strong trend
            
        # Regime alignment
        if regime == "TRENDING UP" and current_price > profile_data['poc']:
            score += 15
        elif regime == "RANGING":
            score += 5
            
        return min(100, score)

class WalkForwardTester:
    # Placeholder for future expansion
    pass

class VWAPCalculator:
    @staticmethod
    def calculate(df):
        # Typical Price * Volume / Cumulative Volume
        v = df['Volume'].values
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        return df.assign(VWAP=(tp * v).cumsum() / v.cumsum())

class StatisticalEdgeCalculator:
    def calculate(self, trades_df):
        if trades_df.empty: return "NO DATA"
        
        wins = trades_df[trades_df['P&L'] > 0]
        losses = trades_df[trades_df['P&L'] <= 0]
        
        win_rate = len(wins) / len(trades_df)
        avg_win = wins['P&L'].mean() if not wins.empty else 0
        avg_loss = abs(losses['P&L'].mean()) if not losses.empty else 0
        
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        if expectancy > 0 and win_rate > 0.5:
            return "✅ EXCELLENT EDGE"
        elif expectancy > 0:
            return "⚠️ WEAK EDGE"
        else:
            return "❌ NO EDGE"

class CorrelationAnalyzer:
    def analyze(self, tickers, period="1mo", interval="1d"):
        # Placeholder: In real app, would fetch data for all tickers
        # and run df.corr()
        return pd.DataFrame() 

class DrawdownProtection:
    def check(self, equity_curve, threshold=0.1):
        if not equity_curve: return False
        
        peak = -999999
        dd = 0
        for pt in equity_curve:
            val = pt['Equity']
            if val > peak: peak = val
            current_dd = (peak - val) / peak
            if current_dd > dd: dd = current_dd
            
        return dd > threshold
