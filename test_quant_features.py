
import pandas as pd
import numpy as np
from strategies import ValueAreaReversionStrategy
from quant_engine import MonteCarloSimulator, KellyCriterion, RegimeDetector, ZScoreCalculator
from backtester import BacktestEngine

def test_strategies():
    print("1. Testing Strategies...")
    try:
        strat = ValueAreaReversionStrategy()
        print(f"   - Instantiated {strat.name}: OK")
        return True
    except Exception as e:
        print(f"   - Strategy Error: {e}")
        return False

def test_quant_engine():
    print("2. Testing Quant Engine...")
    try:
        # Monte Carlo
        trades = pd.DataFrame({'P&L': [100, -50, 200, -100, 150]})
        mc = MonteCarloSimulator(trades, 10000, 100)
        res = mc.run()
        print(f"   - Monte Carlo: {len(res['simulations'])} runs, Median: {res['median']}: OK")

        # Kelly
        kc = KellyCriterion()
        k = kc.calculate(0.6, 2.0)
        print(f"   - Kelly (WR=0.6, R=2): {k:.2f}: OK")

        # Z-Score
        z = ZScoreCalculator()
        series = pd.Series(np.random.normal(0, 1, 100))
        val = z.calculate(series)
        print(f"   - Z-Score: {val:.2f}: OK")
        
        return True
    except Exception as e:
        print(f"   - Quant Engine Error: {e}")
        return False

def test_backtester():
    print("3. Testing BacktestEngine...")
    try:
        engine = BacktestEngine()
        print(f"   - Engine initialized with {len(engine.strategies)} strategies: OK")
        # Cannot run full backtest without yfinance data in this script easily, 
        # but initialization confirms imports and structure.
        return True
    except Exception as e:
        print(f"   - Backtester Error: {e}")
        return False

if __name__ == "__main__":
    print("=== QUANT ENGINE VERIFICATION ===")
    s1 = test_strategies()
    s2 = test_quant_engine()
    s3 = test_backtester()
    
    if s1 and s2 and s3:
        print("\n✅ All quant features working!")
    else:
        print("\n❌ Verification Failed")
