
import pandas as pd
import numpy as np
from volume_profile_engine import VolumeProfileEngine
from strategies import (
    ValueAreaReversionStrategy, 
    POCBounceStrategy, 
    FailedAuctionStrategy, 
    ZScoreMeanReversionStrategy, 
    BreakoutRetestStrategy
)
from quant_engine import (
    MonteCarloSimulator, 
    KellyCriterion, 
    RegimeDetector, 
    ZScoreCalculator, 
    StatisticalEdgeCalculator,
    SetupScorer
)

class BacktestEngine:
    def __init__(self):
        self.strategies = {
            "Value Area Reversion": ValueAreaReversionStrategy(),
            "POC Bounce": POCBounceStrategy(),
            "Failed Auction": FailedAuctionStrategy(),
            "Z-Score Reversion": ZScoreMeanReversionStrategy(),
            "Breakout Retest": BreakoutRetestStrategy()
        }
        self.vp_engine = VolumeProfileEngine()
        self.quant = {
            "kelly": KellyCriterion(),
            "regime": RegimeDetector(),
            "zscore": ZScoreCalculator(),
            "edge": StatisticalEdgeCalculator()
        }

    def run_backtest(self, ticker, strategy_name, period="1mo", interval="1h", capital=10000, risk_pct=0.01):
        # 1. Fetch Data & Profile
        self.vp_engine.ticker = ticker
        self.vp_engine.period = period
        self.vp_engine.interval = interval
        
        df = self.vp_engine.fetch_data()
        if df.empty:
            return {"error": "No data found"}
            
        profile = self.vp_engine.calculate_volume_profile(df)
        poc = self.vp_engine.find_poc(profile)
        val, vah = self.vp_engine.find_value_area(profile)
        
        profile_data = {'poc': poc, 'val': val, 'vah': vah}
        
        # 2. Run Strategy
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return {"error": f"Strategy {strategy_name} not found"}
            
        trades_df, equity_curve = strategy.run(df, profile_data, capital, risk_pct)
        
        if trades_df.empty:
            return {
                "ticker": ticker,
                "strategy": strategy_name,
                "trades": pd.DataFrame(),
                "equity_curve": [],
                "metrics": {"Total Return": "0%", "Win Rate": "0%", "PF": "0"},
                "monte_carlo": {},
                "kelly": 0,
                "regime": "N/A",
                "edge": "NO DATA"
            }

        # 3. Quant Analysis
        # Monte Carlo
        mc = MonteCarloSimulator(trades_df, capital, simulations=2000) # 2000 for speed
        mc_results = mc.run()
        
        # Edge & Kelly
        edge_verdict = self.quant['edge'].calculate(trades_df)
        
        wins = trades_df[trades_df['P&L'] > 0]
        losses = trades_df[trades_df['P&L'] <= 0]
        win_rate = len(wins) / len(trades_df) if len(trades_df) > 0 else 0
        avg_win = wins['P&L'].mean() if not wins.empty else 0
        avg_loss = abs(losses['P&L'].mean()) if not losses.empty else 0
        wl_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        kelly_size = self.quant['kelly'].calculate(win_rate, wl_ratio)
        
        # Regime
        regime = self.quant['regime'].detect(df)
        zscore = self.quant['zscore'].calculate(df['Close'])
        
        # Final Metrics
        final_equity = equity_curve[-1]['Equity']
        total_return = ((final_equity - capital) / capital) * 100
        max_dd = 0 # Todo: implement DD calc
        
        return {
            "ticker": ticker,
            "strategy": strategy_name,
            "trades": trades_df,
            "equity_curve": equity_curve,
            "metrics": {
                "Total Return": f"{total_return:.2f}%",
                "Win Rate": f"{win_rate*100:.1f}%",
                "Profit Factor": f"{wl_ratio:.2f}",
                "Total Trades": len(trades_df),
                "Ending Equity": f"${final_equity:,.2f}"
            },
            "monte_carlo": mc_results,
            "kelly": kelly_size,
            "regime": regime,
            "z_score": zscore,
            "edge": edge_verdict
        }

    def compare_all_strategies(self, ticker, period="1mo", interval="1h", capital=10000):
        results = []
        for name in self.strategies.keys():
            res = self.run_backtest(ticker, name, period, interval, capital)
            if "error" not in res:
                metrics = res['metrics']
                results.append({
                    "Strategy": name,
                    "Return": metrics['Total Return'],
                    "Win Rate": metrics['Win Rate'],
                    "PF": metrics['Profit Factor'],
                    "Trades": metrics['Total Trades'],
                    "Edge": res['edge']
                })
        
        return pd.DataFrame(results).sort_values("Return", ascending=False)
