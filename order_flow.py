"""
Order Flow Analysis Engine
Provides 6 professional order flow analysis tools using free data.
All calculations use OHLCV data from Yahoo Finance.

Features:
1. Delta Analysis - Buy vs sell volume per bar
2. Volume-Weighted Buy/Sell Ratio - Control at each price level
3. Large Block Detection - Institutional footprint
4. Absorption Detection - Hidden support/resistance
5. VWAP + Standard Deviations - Institutional fair value
6. Cumulative Volume Delta (CVD) - Aggregate buyer/seller dominance
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OrderFlowResult:
    """Container for order flow analysis results."""
    delta: pd.DataFrame
    vwap: pd.DataFrame
    large_blocks: pd.DataFrame
    absorption: pd.DataFrame
    summary: Dict


class OrderFlowEngine:
    """
    Professional order flow analysis from OHLCV data.

    Since we don't have Level 2 / tick data (that requires paid feeds),
    we estimate buy/sell pressure using bar-level heuristics:
    - Close > Open = buy bar (volume attributed to buyers)
    - Close < Open = sell bar (volume attributed to sellers)
    - Proportional split based on wick ratios for mixed bars
    """

    def __init__(self, ticker: str, period: str = '5d', interval: str = '1m'):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data = None
        self.results = None

    def fetch_data(self) -> pd.DataFrame:
        """Fetch OHLCV data from Yahoo Finance."""
        self.data = yf.download(
            self.ticker, period=self.period, interval=self.interval,
            progress=False, auto_adjust=True
        )
        if self.data is not None and not self.data.empty:
            # Flatten multi-level columns if present
            if isinstance(self.data.columns, pd.MultiIndex):
                self.data.columns = self.data.columns.get_level_values(0)
        return self.data

    def analyze(self) -> OrderFlowResult:
        """Run all order flow analyses."""
        if self.data is None or self.data.empty:
            self.fetch_data()
        if self.data is None or self.data.empty:
            raise ValueError(f"No data available for {self.ticker}")

        df = self.data.copy()
        df = self._compute_delta(df)
        df = self._compute_vwap(df)
        large_blocks = self._detect_large_blocks(df)
        absorption = self._detect_absorption(df)
        summary = self._generate_summary(df, large_blocks, absorption)

        self.results = OrderFlowResult(
            delta=df,
            vwap=df[['Close', 'VWAP', 'VWAP_1SD_Upper', 'VWAP_1SD_Lower',
                      'VWAP_2SD_Upper', 'VWAP_2SD_Lower']].copy(),
            large_blocks=large_blocks,
            absorption=absorption,
            summary=summary,
        )
        return self.results

    # ----------------------------------------------------------------
    # 1. DELTA ANALYSIS
    # ----------------------------------------------------------------
    def _compute_delta(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Estimate buy/sell volume per bar.

        Method: Use bar direction + wick analysis to split volume.
        - Bullish bar (Close > Open): majority buy
        - Bearish bar (Close < Open): majority sell
        - Wick ratio adjusts the split proportionally
        """
        bar_range = df['High'] - df['Low']
        bar_range = bar_range.replace(0, np.nan)

        body = (df['Close'] - df['Open']).abs()
        body_ratio = body / bar_range

        # Buy ratio: how much of the bar favors buyers
        # Bullish bar: base 0.5 + body contribution
        # Bearish bar: base 0.5 - body contribution
        is_bullish = df['Close'] >= df['Open']
        buy_ratio = np.where(is_bullish, 0.5 + body_ratio * 0.5, 0.5 - body_ratio * 0.5)
        buy_ratio = np.clip(buy_ratio, 0.1, 0.9)  # Never 0% or 100%

        df['Buy_Volume'] = (df['Volume'] * buy_ratio).astype(int)
        df['Sell_Volume'] = (df['Volume'] * (1 - buy_ratio)).astype(int)
        df['Delta'] = df['Buy_Volume'] - df['Sell_Volume']
        df['CVD'] = df['Delta'].cumsum()  # Cumulative Volume Delta
        df['Delta_Pct'] = np.where(
            df['Volume'] > 0,
            (df['Delta'] / df['Volume'] * 100).round(1),
            0
        )
        return df

    # ----------------------------------------------------------------
    # 2. VOLUME-WEIGHTED BUY/SELL RATIO (by price level)
    # ----------------------------------------------------------------
    def get_buy_sell_by_price(self, num_levels: int = 30) -> pd.DataFrame:
        """Get buy/sell volume ratio at each price level."""
        if self.results is None:
            raise ValueError("Run analyze() first")

        df = self.results.delta
        price_min, price_max = df['Low'].min(), df['High'].max()
        levels = np.linspace(price_min, price_max, num_levels)
        level_width = (price_max - price_min) / num_levels

        results = []
        for level in levels:
            mask = (df['Low'] <= level + level_width) & (df['High'] >= level)
            if mask.any():
                buy_vol = df.loc[mask, 'Buy_Volume'].sum()
                sell_vol = df.loc[mask, 'Sell_Volume'].sum()
                total = buy_vol + sell_vol
                results.append({
                    'price': round(level, 2),
                    'buy_volume': int(buy_vol),
                    'sell_volume': int(sell_vol),
                    'total_volume': int(total),
                    'buy_pct': round(buy_vol / total * 100, 1) if total > 0 else 50,
                    'net_delta': int(buy_vol - sell_vol),
                    'control': 'BUYERS' if buy_vol > sell_vol else 'SELLERS',
                })

        return pd.DataFrame(results)

    # ----------------------------------------------------------------
    # 3. LARGE BLOCK DETECTION
    # ----------------------------------------------------------------
    def _detect_large_blocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect unusually large volume bars (institutional activity).
        A bar is flagged if volume > mean + 2 * std_dev.
        """
        vol_mean = df['Volume'].mean()
        vol_std = df['Volume'].std()
        threshold = vol_mean + 2 * vol_std

        large_mask = df['Volume'] >= threshold
        if not large_mask.any():
            return pd.DataFrame()

        blocks = df[large_mask].copy()
        blocks['Vol_Multiple'] = (blocks['Volume'] / vol_mean).round(1)
        blocks['Bar_Type'] = np.where(blocks['Close'] >= blocks['Open'], 'BUY', 'SELL')
        blocks['Price_Impact'] = ((blocks['Close'] - blocks['Open']) / blocks['Open'] * 100).round(3)
        blocks['Significance'] = np.where(
            blocks['Volume'] >= vol_mean + 3 * vol_std, 'EXTREME',
            'LARGE'
        )
        return blocks[['Close', 'Volume', 'Vol_Multiple', 'Bar_Type',
                        'Price_Impact', 'Delta', 'Significance']].copy()

    # ----------------------------------------------------------------
    # 4. ABSORPTION DETECTION
    # ----------------------------------------------------------------
    def _detect_absorption(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect absorption: high volume + minimal price movement.
        This suggests a large player is absorbing the opposing flow.

        Criteria:
        - Volume > 1.5x average
        - Price range < 0.3x average range
        """
        vol_mean = df['Volume'].mean()
        range_series = df['High'] - df['Low']
        range_mean = range_series.mean()

        high_vol = df['Volume'] >= vol_mean * 1.5
        low_range = range_series <= range_mean * 0.3

        absorb_mask = high_vol & low_range
        if not absorb_mask.any():
            return pd.DataFrame()

        absorptions = df[absorb_mask].copy()
        absorptions['Vol_Multiple'] = (absorptions['Volume'] / vol_mean).round(1)
        absorptions['Range'] = (absorptions['High'] - absorptions['Low']).round(4)
        absorptions['Avg_Range'] = round(range_mean, 4)
        absorptions['Range_Ratio'] = (
            (absorptions['High'] - absorptions['Low']) / range_mean
        ).round(2)

        # Determine who is absorbing
        absorptions['Absorber'] = np.where(
            absorptions['Delta'] > 0,
            'BUYERS absorbing sell pressure',
            'SELLERS absorbing buy pressure'
        )

        return absorptions[['Close', 'Volume', 'Vol_Multiple', 'Range',
                            'Range_Ratio', 'Delta', 'Absorber']].copy()

    # ----------------------------------------------------------------
    # 5. VWAP + STANDARD DEVIATIONS
    # ----------------------------------------------------------------
    def _compute_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate VWAP with 1, 2, and 3 standard deviation bands.
        Resets daily for intraday data.
        """
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3

        # For intraday, try to reset daily
        if self.interval in ['1m', '5m', '15m', '30m', '1h']:
            df['Date'] = df.index.date
            groups = df.groupby('Date')

            vwap_list = []
            sd1_upper, sd1_lower = [], []
            sd2_upper, sd2_lower = [], []

            for _, group in groups:
                tp = (group['High'] + group['Low'] + group['Close']) / 3
                cum_vol = group['Volume'].cumsum()
                cum_tp_vol = (tp * group['Volume']).cumsum()

                vwap = cum_tp_vol / cum_vol
                vwap = vwap.replace([np.inf, -np.inf], np.nan).ffill()

                # Standard deviation of price from VWAP, weighted by volume
                squared_diff = ((tp - vwap) ** 2 * group['Volume']).cumsum()
                variance = squared_diff / cum_vol
                sd = np.sqrt(variance)

                vwap_list.extend(vwap.tolist())
                sd1_upper.extend((vwap + sd).tolist())
                sd1_lower.extend((vwap - sd).tolist())
                sd2_upper.extend((vwap + 2 * sd).tolist())
                sd2_lower.extend((vwap - 2 * sd).tolist())

            df['VWAP'] = vwap_list
            df['VWAP_1SD_Upper'] = sd1_upper
            df['VWAP_1SD_Lower'] = sd1_lower
            df['VWAP_2SD_Upper'] = sd2_upper
            df['VWAP_2SD_Lower'] = sd2_lower
            df.drop(columns=['Date'], inplace=True, errors='ignore')

        else:
            # Daily+ data: no reset
            cum_vol = df['Volume'].cumsum()
            cum_tp_vol = (typical_price * df['Volume']).cumsum()
            vwap = cum_tp_vol / cum_vol
            vwap = vwap.replace([np.inf, -np.inf], np.nan).ffill()

            squared_diff = ((typical_price - vwap) ** 2 * df['Volume']).cumsum()
            variance = squared_diff / cum_vol
            sd = np.sqrt(variance)

            df['VWAP'] = vwap
            df['VWAP_1SD_Upper'] = vwap + sd
            df['VWAP_1SD_Lower'] = vwap - sd
            df['VWAP_2SD_Upper'] = vwap + 2 * sd
            df['VWAP_2SD_Lower'] = vwap - 2 * sd

        return df

    # ----------------------------------------------------------------
    # 6. SUMMARY
    # ----------------------------------------------------------------
    def _generate_summary(self, df: pd.DataFrame,
                          large_blocks: pd.DataFrame,
                          absorption: pd.DataFrame) -> Dict:
        """Generate an executive summary of the order flow."""
        total_buy = df['Buy_Volume'].sum()
        total_sell = df['Sell_Volume'].sum()
        total_vol = total_buy + total_sell
        net_delta = total_buy - total_sell

        # Recent momentum (last 20 bars)
        recent = df.tail(20)
        recent_buy = recent['Buy_Volume'].sum()
        recent_sell = recent['Sell_Volume'].sum()
        recent_delta = recent_buy - recent_sell

        # CVD trend
        cvd = df['CVD']
        cvd_start = cvd.iloc[len(cvd)//2] if len(cvd) > 1 else 0
        cvd_end = cvd.iloc[-1]
        cvd_trend = 'RISING' if cvd_end > cvd_start else 'FALLING'

        # Price vs CVD divergence
        price_change = df['Close'].iloc[-1] - df['Close'].iloc[len(df)//2]
        cvd_change = cvd_end - cvd_start
        divergence = False
        divergence_type = 'NONE'
        if price_change > 0 and cvd_change < 0:
            divergence = True
            divergence_type = 'BEARISH (price up, CVD down)'
        elif price_change < 0 and cvd_change > 0:
            divergence = True
            divergence_type = 'BULLISH (price down, CVD up)'

        # Current VWAP position
        current_price = df['Close'].iloc[-1]
        current_vwap = df['VWAP'].iloc[-1]
        vwap_position = 'ABOVE VWAP' if current_price > current_vwap else 'BELOW VWAP'

        return {
            'total_buy_volume': int(total_buy),
            'total_sell_volume': int(total_sell),
            'net_delta': int(net_delta),
            'buy_pct': round(total_buy / total_vol * 100, 1) if total_vol > 0 else 50,
            'sell_pct': round(total_sell / total_vol * 100, 1) if total_vol > 0 else 50,
            'overall_control': 'BUYERS' if net_delta > 0 else 'SELLERS',
            'recent_delta': int(recent_delta),
            'recent_control': 'BUYERS' if recent_delta > 0 else 'SELLERS',
            'cvd_trend': cvd_trend,
            'divergence': divergence,
            'divergence_type': divergence_type,
            'large_blocks_count': len(large_blocks),
            'absorption_count': len(absorption),
            'current_price': float(current_price),
            'vwap': float(current_vwap),
            'vwap_position': vwap_position,
        }


# ----------------------------------------------------------------
# Quick test
# ----------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    engine = OrderFlowEngine('SPY', period='5d', interval='15m')
    engine.fetch_data()
    result = engine.analyze()

    s = result.summary
    print("=" * 60)
    print("ORDER FLOW ANALYSIS: SPY")
    print("=" * 60)

    print(f"\nOverall Control: {s['overall_control']}")
    print(f"Buy Volume:  {s['total_buy_volume']:>12,} ({s['buy_pct']}%)")
    print(f"Sell Volume: {s['total_sell_volume']:>12,} ({s['sell_pct']}%)")
    print(f"Net Delta:   {s['net_delta']:>12,}")

    print(f"\nRecent (20 bars): {s['recent_control']} in control")
    print(f"CVD Trend: {s['cvd_trend']}")
    print(f"Divergence: {s['divergence_type']}")

    print(f"\nVWAP: ${s['vwap']:.2f}")
    print(f"Price: ${s['current_price']:.2f} ({s['vwap_position']})")

    print(f"\nLarge Blocks: {s['large_blocks_count']}")
    if not result.large_blocks.empty:
        for _, row in result.large_blocks.head(5).iterrows():
            print(f"  ${row['Close']:.2f} | {row['Bar_Type']} | "
                  f"{row['Vol_Multiple']}x avg | {row['Significance']}")

    print(f"\nAbsorption Events: {s['absorption_count']}")
    if not result.absorption.empty:
        for _, row in result.absorption.head(5).iterrows():
            print(f"  ${row['Close']:.2f} | {row['Absorber']} | "
                  f"{row['Vol_Multiple']}x vol, {row['Range_Ratio']}x range")

    # Buy/Sell by price
    bs = engine.get_buy_sell_by_price(10)
    print(f"\nBuy/Sell by Price Level:")
    for _, row in bs.iterrows():
        bar = "#" * int(row['buy_pct'] // 5)
        print(f"  ${row['price']:>8.2f} | {bar:<20} | "
              f"Buy {row['buy_pct']}% | {row['control']}")
