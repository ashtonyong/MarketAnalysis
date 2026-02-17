# test_quant_features.py

def test_all():
    from volume_profile_engine import VolumeProfileEngine
    from strategies import ValueAreaReversionStrategy
    from quant_engine import (MonteCarloSimulator, ZScoreCalculator,
                               RegimeDetector, KellyCriterion)
    from backtester import BacktestEngine

    ticker = "SPY"
    print(f"Testing all quant features with {ticker}...\n")

    # Get VP data
    engine = VolumeProfileEngine(ticker, period='1y', interval='1d')
    metrics = engine.get_all_metrics()
    data = engine.data
    poc, vah, val = metrics['poc'], metrics['vah'], metrics['val']

    # Test 1: Strategy
    print("1. Value Area Reversion Strategy...")
    strategy = ValueAreaReversionStrategy(initial_capital=10000)
    results = strategy.run(data, poc, vah, val)
    print(f"   Trades: {results.get('total_trades', 0)}")
    print(f"   Win Rate: {results.get('win_rate', 0):.1f}%")
    print(f"   Return: {results.get('total_return_pct', 0):+.1f}%")

    # Test 2: Monte Carlo
    print("\n2. Monte Carlo Simulation...")
    mc = MonteCarloSimulator()
    mc_results = mc.run(0.65, 150, 100, 100, 1000)
    print(f"   Prob of profit: {mc_results['results']['probability_of_profit']}%")

    # Test 3: Z-Score
    print("\n3. Z-Score Calculator...")
    z = ZScoreCalculator()
    z_results = z.calculate(data, poc)
    print(f"   Z-Score: {z_results['current_z_score']}")
    print(f"   Signal: {z_results['signal']}")

    # Test 4: Regime Detection
    print("\n4. Regime Detection...")
    regime = RegimeDetector()
    r = regime.detect(data)
    print(f"   Regime: {r['regime']}")
    print(f"   Best Strategy: {r['best_strategy']}")

    # Test 5: Kelly
    print("\n5. Kelly Criterion...")
    kelly = KellyCriterion()
    k = kelly.calculate(0.65, 150, 100)
    print(f"   Safe Kelly: {k['safe_kelly_pct']:.1f}%")

    # Test 6: Full Backtest
    print("\n6. Full Backtester...")
    bt = BacktestEngine()
    full = bt.run_backtest(ticker, 'value_area_reversion', '1y')
    print(f"   Return: {full.get('total_return_pct', 0):+.1f}%")
    print(f"   Regime: {full.get('regime', {}).get('regime', 'N/A')}")

    print("\n[OK] All quant features working!")

if __name__ == "__main__":
    test_all()
