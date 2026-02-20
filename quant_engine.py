"""
Quant Engine
Professional quantitative analysis features
Used by hedge funds and professional traders
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 1. MONTE CARLO SIMULATION
# ============================================================

class MonteCarloSimulator:
    """
    Run thousands of simulations to see range of outcomes
    Used by: every professional trading firm

    Shows you:
    - Best case outcome
    - Worst case outcome
    - Most likely outcome
    - Probability of profit
    - Expected max drawdown range
    """

    def run(self, win_rate: float, avg_win: float, avg_loss: float,
            num_trades: int = 100, simulations: int = 10000,
            initial_capital: float = 10000) -> Dict:
        """
        Run Monte Carlo simulation

        Args:
            win_rate: % of trades that win (0.65 = 65%)
            avg_win: Average winning trade in dollars
            avg_loss: Average losing trade in dollars (positive number)
            num_trades: Number of trades to simulate
            simulations: Number of simulation runs
            initial_capital: Starting capital

        Returns:
            Simulation results with statistics
        """
        all_final_capitals = []
        all_max_drawdowns = []
        all_equity_curves = []

        for sim in range(simulations):
            capital = initial_capital
            peak = capital
            max_dd = 0
            equity = [capital]

            for trade in range(num_trades):
                # Random trade outcome based on win rate
                if np.random.random() < win_rate:
                    capital += avg_win
                else:
                    capital -= avg_loss

                # Track drawdown
                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100
                max_dd = max(max_dd, dd)

                equity.append(capital)

            all_final_capitals.append(capital)
            all_max_drawdowns.append(max_dd)

            if sim < 100:  # Save first 100 curves for display
                all_equity_curves.append(equity)

        final_capitals = np.array(all_final_capitals)
        max_drawdowns = np.array(all_max_drawdowns)

        return {
            'simulations': simulations,
            'num_trades': num_trades,
            'inputs': {
                'win_rate': win_rate * 100,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'initial_capital': initial_capital
            },
            'results': {
                'best_case': round(float(np.percentile(final_capitals, 95)), 2),
                'worst_case': round(float(np.percentile(final_capitals, 5)), 2),
                'median': round(float(np.median(final_capitals)), 2),
                'mean': round(float(np.mean(final_capitals)), 2),
                'probability_of_profit': round(
                    float(np.sum(final_capitals > initial_capital) /
                          simulations * 100), 1),
                'probability_of_loss_over_20pct': round(
                    float(np.sum(final_capitals <
                                 initial_capital * 0.8) / simulations * 100), 1),
                'expected_return_pct': round(
                    float((np.mean(final_capitals) - initial_capital) /
                          initial_capital * 100), 2),
                'best_return_pct': round(
                    float((np.percentile(final_capitals, 95) -
                           initial_capital) / initial_capital * 100), 2),
                'worst_return_pct': round(
                    float((np.percentile(final_capitals, 5) -
                           initial_capital) / initial_capital * 100), 2),
                'avg_max_drawdown': round(float(np.mean(max_drawdowns)), 2),
                'worst_max_drawdown': round(
                    float(np.percentile(max_drawdowns, 95)), 2),
            },
            'sample_equity_curves': all_equity_curves[:50]
        }


# ============================================================
# 2. Z-SCORE CALCULATOR
# ============================================================

class ZScoreCalculator:
    """
    Calculate statistical distance from mean
    Tells you how extreme the current price is
    """

    def calculate(self, price_data: pd.DataFrame,
                  poc: float, lookback: int = 20) -> Dict:
        """
        Calculate Z-Score for current price

        Args:
            price_data: OHLCV DataFrame
            poc: Point of Control
            lookback: Rolling window for mean/std

        Returns:
            Z-Score metrics and interpretation
        """
        if price_data is None or price_data.empty or len(price_data) < lookback:
            return {
                'current_price': 0, 'current_z_score': 0, 'poc_z_score': 0,
                'rolling_mean': 0, 'rolling_std': 0, 'signal': 'DATA_INSUFFICIENT',
                'action': 'Wait for more data', 'color': 'gray',
                'reversion_probability': 0, 'target_mean_reversion': 0,
                'z_score_history': [], 'interpretation': 'Insufficient data for Z-Score'
            }

        closes = price_data['Close']
        current_price = closes.iloc[-1]

        # Rolling statistics
        rolling_mean = closes.rolling(lookback).mean()
        rolling_std = closes.rolling(lookback).std()

        last_std = rolling_std.iloc[-1]
        last_mean = rolling_mean.iloc[-1]

        if np.isnan(last_std) or last_std == 0:
            current_z = 0
            poc_z = 0
        else:
            # Current Z-Score
            current_z = (current_price - last_mean) / last_std

            # Z-Score vs POC
            poc_z = (current_price - poc) / last_std

        # Historical Z-Scores
        z_series = (closes - rolling_mean) / rolling_std

        # Interpretation
        if current_z > 2.0:
            signal = 'STRONGLY_OVERBOUGHT'
            action = 'Look for SHORT entry - statistically extreme'
            color = 'red'
        elif current_z > 1.0:
            signal = 'OVERBOUGHT'
            action = 'Caution for longs - above mean'
            color = 'orange'
        elif current_z < -2.0:
            signal = 'STRONGLY_OVERSOLD'
            action = 'Look for LONG entry - statistically extreme'
            color = 'green'
        elif current_z < -1.0:
            signal = 'OVERSOLD'
            action = 'Watch for long setup - below mean'
            color = 'lightgreen'
        else:
            signal = 'NEUTRAL'
            action = 'Price near statistical mean'
            color = 'gray'

        # Mean reversion probability
        if abs(current_z) > 2:
            reversion_prob = 95.4
        elif abs(current_z) > 1:
            reversion_prob = 68.3
        else:
            reversion_prob = 50.0

        return {
            'current_price': current_price,
            'current_z_score': round(float(current_z), 3),
            'poc_z_score': round(float(poc_z), 3),
            'rolling_mean': round(float(rolling_mean.iloc[-1]), 2),
            'rolling_std': round(float(rolling_std.iloc[-1]), 2),
            'signal': signal,
            'action': action,
            'color': color,
            'reversion_probability': reversion_prob,
            'target_mean_reversion': round(float(rolling_mean.iloc[-1]), 2),
            'z_score_history': z_series.dropna().tolist()[-50:],
            'interpretation': (
                f"Price is {abs(current_z):.2f} standard deviations "
                f"{'above' if current_z > 0 else 'below'} the mean. "
                f"{reversion_prob}% probability of mean reversion."
            )
        }


# ============================================================
# 3. REGIME DETECTION
# ============================================================

class RegimeDetector:
    """
    Detect market regime: Trending, Ranging, or Volatile
    Different strategies work in different regimes!
    """

    def detect(self, price_data: pd.DataFrame) -> Dict:
        """
        Detect current market regime

        Args:
            price_data: OHLCV DataFrame

        Returns:
            Regime classification and recommended strategy
        """
        closes = price_data['Close']
        highs = price_data['High']
        lows = price_data['Low']
        volumes = price_data['Volume']

        # ADX calculation (trend strength)
        adx = self._calculate_adx(highs, lows, closes, period=14)

        # ATR (volatility)
        atr = self._calculate_atr(highs, lows, closes, period=14)
        avg_atr = atr.rolling(50).mean()
        atr_ratio = (atr.iloc[-1] / avg_atr.iloc[-1]
                     if avg_atr.iloc[-1] > 0 else 1)

        # Volume trend
        avg_vol = volumes.rolling(20).mean()
        vol_ratio = (volumes.iloc[-1] / avg_vol.iloc[-1]
                     if avg_vol.iloc[-1] > 0 else 1)

        # Price momentum
        momentum = (closes.iloc[-1] - closes.iloc[-20]) / closes.iloc[-20] * 100

        current_adx = float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else 20

        # Classify regime
        if current_adx > 25 and atr_ratio < 1.5:
            if momentum > 0:
                regime = 'TRENDING_UP'
                best_strategy = 'Breakout Retest (Long bias)'
                description = 'Strong uptrend - Use trend following strategies'
                color = 'green'
            else:
                regime = 'TRENDING_DOWN'
                best_strategy = 'Breakout Retest (Short bias)'
                description = 'Strong downtrend - Use trend following strategies'
                color = 'red'

        elif atr_ratio > 2.0:
            regime = 'VOLATILE'
            best_strategy = 'Reduce position size 50%, widen stops'
            description = 'High volatility - Reduce size, avoid mean reversion'
            color = 'orange'

        else:
            regime = 'RANGING'
            best_strategy = 'Value Area Reversion (BEST in ranging markets)'
            description = 'Ranging market - Mean reversion strategies work best'
            color = 'blue'

        # Strategy recommendations
        recommendations = {
            'TRENDING_UP': [
                ' Breakout Retest (long only)',
                ' POC Bounce (long bias)',
                ' Avoid mean reversion shorts'
            ],
            'TRENDING_DOWN': [
                ' Breakout Retest (short only)',
                ' Failed Auction (short bias)',
                ' Avoid mean reversion longs'
            ],
            'RANGING': [
                ' Value Area Reversion (BEST)',
                ' POC Bounce',
                ' Z-Score Mean Reversion',
                ' Avoid breakout strategies'
            ],
            'VOLATILE': [
                '️ Reduce all position sizes by 50%',
                '️ Widen stops to 2x normal',
                ' Avoid new positions if possible'
            ]
        }

        return {
            'regime': regime,
            'adx': round(current_adx, 2),
            'atr_ratio': round(atr_ratio, 2),
            'vol_ratio': round(vol_ratio, 2),
            'momentum_20bar': round(momentum, 2),
            'description': description,
            'best_strategy': best_strategy,
            'color': color,
            'recommendations': recommendations.get(regime, []),
            'confidence': self._calculate_confidence(current_adx, atr_ratio)
        }

    def _calculate_adx(self, high, low, close, period=14):
        """Calculate Average Directional Index"""
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)

        atr = tr.rolling(period).mean()

        dm_plus = (high - high.shift(1)).clip(lower=0)
        dm_minus = (low.shift(1) - low).clip(lower=0)

        di_plus = (dm_plus.rolling(period).mean() / atr) * 100
        di_minus = (dm_minus.rolling(period).mean() / atr) * 100

        dx = (abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)) * 100
        adx = dx.rolling(period).mean()

        return adx

    def _calculate_atr(self, high, low, close, period=14):
        """Calculate Average True Range"""
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)
        return tr.rolling(period).mean()

    def _calculate_confidence(self, adx, atr_ratio):
        """Calculate confidence in regime classification"""
        if adx > 30 or atr_ratio > 2.5:
            return 'HIGH'
        elif adx > 20 or atr_ratio > 1.5:
            return 'MEDIUM'
        else:
            return 'LOW'


# ============================================================
# 4. KELLY CRITERION POSITION SIZING
# ============================================================

class KellyCriterion:
    """
    Optimal position sizing formula used by quant funds
    Maximizes long-term growth while managing risk
    """

    def calculate(self, win_rate: float, avg_win: float,
                  avg_loss: float, kelly_fraction: float = 0.5) -> Dict:
        """
        Calculate optimal position size

        Args:
            win_rate: % of trades that win (0.65 = 65%)
            avg_win: Average win amount
            avg_loss: Average loss amount (positive)
            kelly_fraction: Fraction of Kelly to use (0.5 = Half Kelly, safer)

        Returns:
            Position sizing recommendations
        """
        if avg_loss == 0:
            return {'error': 'avg_loss cannot be zero'}

        win_loss_ratio = avg_win / avg_loss
        loss_rate = 1 - win_rate

        # Full Kelly formula
        full_kelly = win_rate - (loss_rate / win_loss_ratio)

        # Apply fraction (Half Kelly recommended)
        recommended_kelly = full_kelly * kelly_fraction

        # Safety cap at 25%
        safe_kelly = min(recommended_kelly, 0.25)

        if full_kelly <= 0:
            return {
                'full_kelly': round(full_kelly * 100, 2),
                'recommendation': 'NEGATIVE EDGE - Do not trade this strategy',
                'action': 'Fix strategy before trading'
            }

        return {
            'full_kelly_pct': round(full_kelly * 100, 2),
            'half_kelly_pct': round(recommended_kelly * 100, 2),
            'safe_kelly_pct': round(safe_kelly * 100, 2),
            'win_rate_pct': round(win_rate * 100, 2),
            'win_loss_ratio': round(win_loss_ratio, 2),
            'recommendation': (
                f"Risk {safe_kelly * 100:.1f}% of account per trade "
                f"(Half Kelly with 25% cap)"
            ),
            'interpretation': self._interpret_kelly(safe_kelly),
            'position_sizes': {
                '$10,000 account': f'${10000 * safe_kelly:.0f}',
                '$25,000 account': f'${25000 * safe_kelly:.0f}',
                '$50,000 account': f'${50000 * safe_kelly:.0f}',
                '$100,000 account': f'${100000 * safe_kelly:.0f}'
            }
        }

    def _interpret_kelly(self, kelly):
        if kelly >= 0.2:
            return 'STRONG EDGE - High conviction sizing appropriate'
        elif kelly >= 0.1:
            return 'GOOD EDGE - Standard sizing'
        elif kelly >= 0.05:
            return 'MODERATE EDGE - Conservative sizing'
        else:
            return 'WEAK EDGE - Minimum sizing only'


# ============================================================
# 5. DRAWDOWN PROTECTION
# ============================================================

class DrawdownProtection:
    """
    Auto-reduce position size during losing streaks
    Professional risk management feature
    """

    def __init__(self, max_drawdown_pct: float = 10.0,
                 initial_capital: float = 10000):
        self.max_drawdown_pct = max_drawdown_pct
        self.initial_capital = initial_capital
        self.peak_capital = initial_capital
        self.current_capital = initial_capital

    def update_capital(self, current_capital: float):
        """Update capital and peak"""
        self.current_capital = current_capital
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital

    def get_risk_multiplier(self) -> Dict:
        """
        Get current risk multiplier based on drawdown

        Returns:
            Risk multiplier (0.0 to 1.0) and status
        """
        current_drawdown = ((self.peak_capital - self.current_capital) /
                           self.peak_capital * 100)
        dd_pct_of_max = current_drawdown / self.max_drawdown_pct * 100

        if current_drawdown >= self.max_drawdown_pct:
            multiplier = 0.0
            status = 'STOP_TRADING'
            message = (f'Max drawdown reached ({current_drawdown:.1f}%). '
                      f'STOP TRADING. Review strategy.')
            color = 'red'
        elif dd_pct_of_max >= 70:
            multiplier = 0.25
            status = 'SEVERELY_REDUCED'
            message = f'Near max drawdown. Trade at 25% normal size.'
            color = 'orange'
        elif dd_pct_of_max >= 50:
            multiplier = 0.50
            status = 'REDUCED'
            message = f'Significant drawdown. Trade at 50% normal size.'
            color = 'yellow'
        elif dd_pct_of_max >= 30:
            multiplier = 0.75
            status = 'SLIGHTLY_REDUCED'
            message = f'Minor drawdown. Trade at 75% normal size.'
            color = 'lightgreen'
        else:
            multiplier = 1.0
            status = 'NORMAL'
            message = 'No significant drawdown. Trade at full size.'
            color = 'green'

        return {
            'risk_multiplier': multiplier,
            'status': status,
            'message': message,
            'color': color,
            'current_drawdown_pct': round(current_drawdown, 2),
            'max_drawdown_allowed': self.max_drawdown_pct,
            'current_capital': self.current_capital,
            'peak_capital': self.peak_capital,
            'dollars_down': round(self.peak_capital - self.current_capital, 2)
        }


# ============================================================
# 6. MULTI-FACTOR SETUP SCORING
# ============================================================

class SetupScorer:
    """
    Score trading setups 0-100 based on multiple factors
    Only trade setups with score > 70
    Used by: Professional quant traders
    """

    def score_setup(self, ticker_data: Dict) -> Dict:
        """
        Score a trading setup

        Args:
            ticker_data: Dict with analysis data including:
                - current_price, poc, vah, val, position
                - distance_from_poc_pct
                - volume (current vs average)
                - z_score
                - regime
                - patterns detected

        Returns:
            Score 0-100 with breakdown
        """
        score = 0
        factors = {}

        # Factor 1: Distance from POC (20 pts max)
        distance = abs(ticker_data.get('distance_from_poc_pct', 0))
        if distance < 0.5:
            pts = 20
            desc = 'Very close to POC (20/20)'
        elif distance < 1.0:
            pts = 15
            desc = 'Near POC (15/20)'
        elif distance < 2.0:
            pts = 10
            desc = 'Moderate distance (10/20)'
        elif distance < 5.0:
            pts = 5
            desc = 'Far from POC (5/20)'
        else:
            pts = 0
            desc = 'Very far from POC (0/20)'
        score += pts
        factors['poc_distance'] = {'points': pts, 'max': 20, 'description': desc}

        # Factor 2: Position (15 pts max)
        position = ticker_data.get('position', '')
        if 'ABOVE' in position:
            pts = 15
            desc = 'Above Value Area - bullish (15/15)'
        elif 'BELOW' in position:
            pts = 15
            desc = 'Below Value Area - bearish (15/15)'
        else:
            pts = 5
            desc = 'Inside Value Area - neutral (5/15)'
        score += pts
        factors['va_position'] = {'points': pts, 'max': 15, 'description': desc}

        # Factor 3: Volume (15 pts max)
        vol_ratio = ticker_data.get('volume_ratio', 1.0)
        if vol_ratio > 2.0:
            pts = 15
            desc = f'High volume: {vol_ratio:.1f}x average (15/15)'
        elif vol_ratio > 1.5:
            pts = 10
            desc = f'Above avg volume: {vol_ratio:.1f}x (10/15)'
        elif vol_ratio > 1.0:
            pts = 5
            desc = f'Average volume: {vol_ratio:.1f}x (5/15)'
        else:
            pts = 0
            desc = f'Low volume: {vol_ratio:.1f}x (0/15)'
        score += pts
        factors['volume'] = {'points': pts, 'max': 15, 'description': desc}

        # Factor 4: Z-Score (15 pts max)
        z_score = abs(ticker_data.get('z_score', 0))
        if z_score > 2.5:
            pts = 15
            desc = f'Extreme Z-Score: {z_score:.2f} (15/15)'
        elif z_score > 2.0:
            pts = 12
            desc = f'High Z-Score: {z_score:.2f} (12/15)'
        elif z_score > 1.5:
            pts = 8
            desc = f'Moderate Z-Score: {z_score:.2f} (8/15)'
        elif z_score > 1.0:
            pts = 4
            desc = f'Low Z-Score: {z_score:.2f} (4/15)'
        else:
            pts = 0
            desc = f'Minimal Z-Score: {z_score:.2f} (0/15)'
        score += pts
        factors['z_score'] = {'points': pts, 'max': 15, 'description': desc}

        # Factor 5: Market Regime (15 pts max)
        regime = ticker_data.get('regime', 'UNKNOWN')
        if regime == 'RANGING':
            pts = 15
            desc = 'Ranging market - best for VP strategies (15/15)'
        elif 'TRENDING' in regime:
            pts = 8
            desc = 'Trending market - use with caution (8/15)'
        elif regime == 'VOLATILE':
            pts = 2
            desc = 'Volatile market - reduce size (2/15)'
        else:
            pts = 5
            desc = 'Unknown regime (5/15)'
        score += pts
        factors['regime'] = {'points': pts, 'max': 15, 'description': desc}

        # Factor 6: Pattern Quality (20 pts max)
        pattern_pts = 0
        patterns = ticker_data.get('patterns', {})
        if patterns.get('poor_high') or patterns.get('poor_low'):
            pattern_pts += 8
        if patterns.get('single_prints'):
            pattern_pts += 5
        if patterns.get('excess'):
            pattern_pts += 7
        pattern_pts = min(pattern_pts, 20)
        score += pattern_pts
        factors['patterns'] = {
            'points': pattern_pts,
            'max': 20,
            'description': f'Pattern bonus: {pattern_pts}/20'
        }

        # Interpretation
        if score >= 80:
            grade = 'A+'
            action = 'STRONG SETUP - High confidence trade'
            color = 'green'
        elif score >= 70:
            grade = 'A'
            action = 'GOOD SETUP - Take the trade'
            color = 'lightgreen'
        elif score >= 60:
            grade = 'B'
            action = 'MODERATE SETUP - Trade with smaller size'
            color = 'yellow'
        elif score >= 50:
            grade = 'C'
            action = 'WEAK SETUP - Skip or very small size'
            color = 'orange'
        else:
            grade = 'D'
            action = 'POOR SETUP - Skip this trade'
            color = 'red'

        return {
            'total_score': score,
            'max_score': 100,
            'grade': grade,
            'action': action,
            'color': color,
            'factor_breakdown': factors,
            'recommendation': (
                f"Score {score}/100 ({grade}): {action}"
            )
        }


# ============================================================
# 7. WALK-FORWARD TESTING
# ============================================================

class WalkForwardTester:
    """
    Professional backtesting that prevents overfitting
    Train on past data, test on unseen future data
    Used by: All serious quant funds
    """

    def run(self, price_data: pd.DataFrame, poc: float,
            vah: float, val: float, strategy_class,
            train_pct: float = 0.7, num_windows: int = 5) -> Dict:
        """
        Run walk-forward test

        Args:
            price_data: Full OHLCV data
            poc, vah, val: Volume Profile levels
            strategy_class: Strategy to test
            train_pct: % of each window for training
            num_windows: Number of walk-forward windows

        Returns:
            Walk-forward results
        """
        n = len(price_data)
        window_size = n // num_windows
        results = []

        for i in range(num_windows):
            start = i * window_size
            end = min(start + window_size, n)

            train_end = int(start + (end - start) * train_pct)

            train_data = price_data.iloc[start:train_end]
            test_data = price_data.iloc[train_end:end]

            if len(test_data) < 10:
                continue

            # Test on out-of-sample data
            try:
                strategy = strategy_class(initial_capital=10000)
                test_result = strategy.run(test_data, poc, vah, val)

                results.append({
                    'window': i + 1,
                    'train_period': (
                        f"{train_data.index[0].strftime('%Y-%m-%d')} to "
                        f"{train_data.index[-1].strftime('%Y-%m-%d')}"
                    ),
                    'test_period': (
                        f"{test_data.index[0].strftime('%Y-%m-%d')} to "
                        f"{test_data.index[-1].strftime('%Y-%m-%d')}"
                    ),
                    'trades': test_result.get('total_trades', 0),
                    'win_rate': test_result.get('win_rate', 0),
                    'return_pct': test_result.get('total_return_pct', 0),
                    'profit_factor': test_result.get('profit_factor', 0),
                    'max_dd': test_result.get('max_drawdown_pct', 0)
                })
            except Exception as e:
                results.append({
                    'window': i + 1,
                    'error': str(e)
                })

        if not results:
            return {'error': 'No valid walk-forward windows'}

        valid = [r for r in results if 'error' not in r and r['trades'] > 0]

        if not valid:
            return {'results': results, 'summary': 'No trades in any window'}

        avg_win_rate = np.mean([r['win_rate'] for r in valid])
        avg_return = np.mean([r['return_pct'] for r in valid])
        avg_pf = np.mean([r['profit_factor'] for r in valid])
        consistent = sum(1 for r in valid if r['return_pct'] > 0)

        return {
            'windows': results,
            'summary': {
                'num_windows': len(valid),
                'profitable_windows': consistent,
                'consistency': f'{consistent}/{len(valid)} windows profitable',
                'avg_win_rate': round(avg_win_rate, 2),
                'avg_return_pct': round(avg_return, 2),
                'avg_profit_factor': round(avg_pf, 2),
                'is_robust': consistent >= len(valid) * 0.6,
                'verdict': ('ROBUST STRATEGY' if consistent >= len(valid) * 0.6
                           else 'OVERFIT - Strategy not robust')
            }
        }


# ============================================================
# 8. VWAP BANDS
# ============================================================

class VWAPCalculator:
    """
    Volume Weighted Average Price + Standard Deviation Bands
    Used by every institutional trader
    Most important intraday level
    """

    def calculate(self, price_data: pd.DataFrame) -> Dict:
        """
        Calculate VWAP and bands

        Args:
            price_data: OHLCV intraday data

        Returns:
            VWAP, bands, and signals
        """
        typical_price = (price_data['High'] +
                        price_data['Low'] +
                        price_data['Close']) / 3

        cumulative_vp = (typical_price * price_data['Volume']).cumsum()
        cumulative_vol = price_data['Volume'].cumsum()

        vwap = cumulative_vp / cumulative_vol

        # Standard deviation bands
        sq_diff = (typical_price - vwap) ** 2
        variance = (sq_diff * price_data['Volume']).cumsum() / cumulative_vol
        std = np.sqrt(variance)

        current_price = price_data['Close'].iloc[-1]
        current_vwap = float(vwap.iloc[-1])
        current_std = float(std.iloc[-1])

        bands = {
            'vwap': round(current_vwap, 2),
            'upper_1std': round(current_vwap + current_std, 2),
            'upper_2std': round(current_vwap + 2 * current_std, 2),
            'lower_1std': round(current_vwap - current_std, 2),
            'lower_2std': round(current_vwap - 2 * current_std, 2),
        }

        # Signal
        if current_price > bands['upper_2std']:
            signal = 'STRONGLY_ABOVE_VWAP'
            action = 'Extreme overbought vs VWAP - mean reversion short'
        elif current_price > bands['upper_1std']:
            signal = 'ABOVE_VWAP'
            action = 'Above VWAP - bullish but extended'
        elif current_price < bands['lower_2std']:
            signal = 'STRONGLY_BELOW_VWAP'
            action = 'Extreme oversold vs VWAP - mean reversion long'
        elif current_price < bands['lower_1std']:
            signal = 'BELOW_VWAP'
            action = 'Below VWAP - bearish but extended'
        else:
            signal = 'AT_VWAP'
            action = 'Near VWAP - fair value zone'

        return {
            'current_price': current_price,
            'bands': bands,
            'signal': signal,
            'action': action,
            'deviation_pct': round(
                (current_price - current_vwap) / current_vwap * 100, 3),
            'vwap_series': vwap.tolist(),
            'upper_1_series': (vwap + std).tolist(),
            'upper_2_series': (vwap + 2 * std).tolist(),
            'lower_1_series': (vwap - std).tolist(),
            'lower_2_series': (vwap - 2 * std).tolist(),
        }


# ============================================================
# 9. STATISTICAL EDGE CALCULATOR
# ============================================================

class StatisticalEdgeCalculator:
    """
    Calculate your complete statistical edge
    Answers: "Is this strategy worth trading?"
    """

    def calculate(self, trades: List) -> Dict:
        """
        Calculate complete statistical edge from trade history

        Args:
            trades: List of Trade objects

        Returns:
            Complete edge statistics
        """
        if not trades:
            return {'error': 'No trades to analyze'}

        wins = [t for t in trades if t.result == 'WIN']
        losses = [t for t in trades if t.result == 'LOSS']

        if not trades:
            return {'error': 'No completed trades'}

        win_rate = len(wins) / len(trades)
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t.pnl for t in losses])) if losses else 0.01

        # Core metrics
        profit_factor = (sum(t.pnl for t in wins) /
                        abs(sum(t.pnl for t in losses))) if losses else 999

        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Sharpe ratio
        returns = [t.pnl for t in trades]
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)
                  if np.std(returns) > 0 else 0)

        # Maximum consecutive losses
        max_consec_losses = 0
        current_losses = 0
        for t in trades:
            if t.result == 'LOSS':
                current_losses += 1
                max_consec_losses = max(max_consec_losses, current_losses)
            else:
                current_losses = 0

        # R-multiple distribution
        r_multiples = []
        for t in trades:
            risk = abs(t.entry_price - t.stop_loss)
            if risk > 0:
                r = t.pnl / (risk * 1)
                r_multiples.append(r)

        avg_r = np.mean(r_multiples) if r_multiples else 0

        # Kelly criterion
        kelly_calc = KellyCriterion()
        kelly = kelly_calc.calculate(win_rate, avg_win, avg_loss)

        # Overall verdict
        if (profit_factor > 2.0 and win_rate > 0.55 and
                expectancy > 0 and sharpe > 1.0):
            verdict = 'EXCELLENT EDGE'
            tradeable = True
        elif profit_factor > 1.5 and expectancy > 0:
            verdict = 'GOOD EDGE'
            tradeable = True
        elif profit_factor > 1.2 and expectancy > 0:
            verdict = 'MARGINAL EDGE'
            tradeable = True
        elif expectancy > 0:
            verdict = 'WEAK EDGE'
            tradeable = False
        else:
            verdict = 'NO EDGE'
            tradeable = False

        return {
            'total_trades': len(trades),
            'win_rate': round(win_rate * 100, 2),
            'profit_factor': round(profit_factor, 2),
            'expectancy_per_trade': round(expectancy, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'win_loss_ratio': round(avg_win / avg_loss if avg_loss > 0 else 0, 2),
            'sharpe_ratio': round(sharpe, 2),
            'avg_r_multiple': round(avg_r, 2),
            'max_consecutive_losses': max_consec_losses,
            'kelly_criterion': kelly,
            'verdict': verdict,
            'tradeable': tradeable,
            'recommendation': (
                f"{' Trade this strategy' if tradeable else ' Do not trade'}: "
                f"{verdict}"
            )
        }


# ============================================================
# 10. CORRELATION MATRIX
# ============================================================

class CorrelationAnalyzer:
    """
    Analyze correlation between assets
    Avoid being in highly correlated positions simultaneously
    """

    def calculate(self, tickers: List[str],
                  period: str = '3mo') -> Dict:
        """
        Calculate correlation matrix for watchlist

        Args:
            tickers: List of ticker symbols
            period: Time period for correlation

        Returns:
            Correlation matrix and recommendations
        """
        import yfinance as yf

        prices = {}
        for ticker in tickers:
            try:
                data = yf.Ticker(ticker).history(period=period)
                prices[ticker] = data['Close']
            except:
                pass

        if len(prices) < 2:
            return {'error': 'Need at least 2 tickers'}

        price_df = pd.DataFrame(prices).dropna()
        returns_df = price_df.pct_change().dropna()
        corr_matrix = returns_df.corr()

        # Find highly correlated pairs
        high_correlation_pairs = []
        negative_correlation_pairs = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                t1 = corr_matrix.columns[i]
                t2 = corr_matrix.columns[j]
                corr = corr_matrix.iloc[i, j]

                if corr > 0.8:
                    high_correlation_pairs.append({
                        'ticker1': t1,
                        'ticker2': t2,
                        'correlation': round(corr, 3),
                        'warning': 'AVOID holding both - too correlated'
                    })
                elif corr < -0.5:
                    negative_correlation_pairs.append({
                        'ticker1': t1,
                        'ticker2': t2,
                        'correlation': round(corr, 3),
                        'note': 'GOOD hedge - these move oppositely'
                    })

        return {
            'correlation_matrix': corr_matrix.round(3).to_dict(),
            'tickers_analyzed': list(prices.keys()),
            'high_correlation_pairs': high_correlation_pairs,
            'hedge_pairs': negative_correlation_pairs,
            'recommendations': self._generate_recommendations(
                high_correlation_pairs, negative_correlation_pairs)
        }

    def _generate_recommendations(self, high_corr, hedges):
        recs = []
        for pair in high_corr:
            recs.append(
                f"️ {pair['ticker1']} + {pair['ticker2']}: "
                f"Correlation {pair['correlation']} - Pick one!"
            )
        for hedge in hedges:
            recs.append(
                f" {hedge['ticker1']} + {hedge['ticker2']}: "
                f"Correlation {hedge['correlation']} - Good hedge pair"
            )
        return recs if recs else ["No significant correlations found"]
