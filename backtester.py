"""
Main Backtester
Connects strategies with quant features
Provides unified interface
"""

import pandas as pd
from typing import Dict, List
from strategies import (
    ValueAreaReversionStrategy,
    POCBounceStrategy,
    FailedAuctionStrategy,
    ZScoreMeanReversionStrategy,
    BreakoutRetestStrategy
)
from quant_engine import (
    MonteCarloSimulator,
    ZScoreCalculator,
    RegimeDetector,
    KellyCriterion,
    DrawdownProtection,
    SetupScorer,
    WalkForwardTester,
    VWAPCalculator,
    StatisticalEdgeCalculator,
    CorrelationAnalyzer
)
from volume_profile_engine import VolumeProfileEngine


class BacktestEngine:
    """Main backtesting engine"""

    STRATEGIES = {
        'value_area_reversion': ValueAreaReversionStrategy,
        'poc_bounce': POCBounceStrategy,
        'failed_auction': FailedAuctionStrategy,
        'zscore_mean_reversion': ZScoreMeanReversionStrategy,
        'breakout_retest': BreakoutRetestStrategy
    }

    def run_backtest(self, ticker: str, strategy_name: str,
                     period: str = '1y', interval: str = '1d',
                     initial_capital: float = 10000,
                     risk_per_trade: float = 1.0) -> Dict:
        """
        Run complete backtest

        Args:
            ticker: Stock symbol
            strategy_name: Strategy to test
            period: Backtest period
            interval: Bar interval
            initial_capital: Starting capital
            risk_per_trade: % risk per trade

        Returns:
            Complete backtest results
        """
        # Get volume profile
        engine = VolumeProfileEngine(ticker, period=period, interval=interval)
        metrics = engine.get_all_metrics()
        price_data = engine.data

        poc = metrics['poc']
        vah = metrics['vah']
        val = metrics['val']

        # Get strategy class
        StrategyClass = self.STRATEGIES.get(strategy_name)
        if not StrategyClass:
            return {'error': f'Unknown strategy: {strategy_name}'}

        # Run strategy
        strategy = StrategyClass(
            initial_capital=initial_capital,
            risk_per_trade_pct=risk_per_trade
        )
        results = strategy.run(price_data, poc, vah, val)

        # Add quant analysis
        if 'trades' in results and results['trades']:
            # Statistical edge
            edge_calc = StatisticalEdgeCalculator()
            results['statistical_edge'] = edge_calc.calculate(results['trades'])

            # Kelly criterion
            kelly = KellyCriterion()
            results['kelly_criterion'] = kelly.calculate(
                results['win_rate'] / 100,
                results['avg_win_dollars'],
                results['avg_loss_dollars']
            )

            # Monte Carlo
            mc = MonteCarloSimulator()
            results['monte_carlo'] = mc.run(
                win_rate=results['win_rate'] / 100,
                avg_win=results['avg_win_dollars'],
                avg_loss=results['avg_loss_dollars'],
                num_trades=results['total_trades'],
                simulations=5000
            )

        # Regime detection
        regime = RegimeDetector()
        results['regime'] = regime.detect(price_data)

        # Z-Score
        z_calc = ZScoreCalculator()
        results['z_score_analysis'] = z_calc.calculate(price_data, poc)

        results['ticker'] = ticker
        results['strategy'] = strategy_name
        results['period'] = period
        results['interval'] = interval
        results['poc'] = poc
        results['vah'] = vah
        results['val'] = val

        return results

    def compare_all_strategies(self, ticker: str, period: str = '1y',
                               interval: str = '1d',
                               initial_capital: float = 10000) -> Dict:
        """Run all 5 strategies and compare"""
        comparison = []

        for strategy_name in self.STRATEGIES:
            try:
                result = self.run_backtest(
                    ticker, strategy_name, period,
                    interval, initial_capital
                )
                if 'error' not in result:
                    comparison.append({
                        'strategy': strategy_name,
                        'total_trades': result.get('total_trades', 0),
                        'win_rate': result.get('win_rate', 0),
                        'total_return_pct': result.get('total_return_pct', 0),
                        'profit_factor': result.get('profit_factor', 0),
                        'max_drawdown_pct': result.get('max_drawdown_pct', 0),
                        'sharpe_ratio': result.get('sharpe_ratio', 0),
                        'expectancy': result.get('expectancy_per_trade', 0)
                    })
            except Exception as e:
                print(f"Error with {strategy_name}: {e}")

        # Sort by profit factor
        comparison.sort(key=lambda x: x['profit_factor'], reverse=True)

        return {
            'ticker': ticker,
            'period': period,
            'comparison': comparison,
            'best_strategy': comparison[0] if comparison else None
        }
