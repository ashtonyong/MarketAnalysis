"""
Multi-Timeframe Volume Profile Analysis
Computes VP across 3 timeframes and finds confluent levels.
When POC/VAH/VAL align across timeframes, they're extremely strong S/R.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple


class MultiTimeframeAnalyzer:
    """Analyze volume profile across multiple timeframes."""

    TIMEFRAME_CONFIGS = {
        '15m': {'period': '5d', 'interval': '15m', 'label': '15-Minute'},
        '1h':  {'period': '1mo', 'interval': '1h', 'label': '1-Hour'},
        '4h':  {'period': '3mo', 'interval': '1h', 'label': '4-Hour'},  # Approximate with 1h
        '1d':  {'period': '6mo', 'interval': '1d', 'label': 'Daily'},
        '1w':  {'period': '1y', 'interval': '1wk', 'label': 'Weekly'},
    }

    def __init__(self, ticker: str, timeframes: List[str] = None):
        self.ticker = ticker
        self.timeframes = timeframes or ['15m', '1h', '1d']
        self.results = {}

    def analyze(self) -> Dict:
        """Run VP analysis on each timeframe and find confluences."""
        for tf in self.timeframes:
            config = self.TIMEFRAME_CONFIGS.get(tf)
            if not config:
                continue
            try:
                data = yf.download(
                    self.ticker, period=config['period'],
                    interval=config['interval'], progress=False, auto_adjust=True
                )
                if data is not None and not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)

                    profile = self._compute_profile(data)
                    self.results[tf] = {
                        'label': config['label'],
                        'data': data,
                        'profile': profile,
                        'poc': profile['poc'],
                        'vah': profile['vah'],
                        'val': profile['val'],
                        'current_price': float(data['Close'].iloc[-1]),
                    }
            except Exception as e:
                self.results[tf] = {'label': config.get('label', tf), 'error': str(e)}

        # Find confluences
        confluences = self._find_confluences()

        return {
            'timeframes': self.results,
            'confluences': confluences,
            'strongest_levels': self._rank_levels(confluences),
        }

    def _compute_profile(self, data: pd.DataFrame, bins: int = 50) -> Dict:
        """Compute volume profile for a dataset."""
        price_min, price_max = data['Low'].min(), data['High'].max()
        bin_edges = np.linspace(price_min, price_max, bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        volumes = np.zeros(bins)
        for _, row in data.iterrows():
            mask = (bin_centers >= row['Low']) & (bin_centers <= row['High'])
            matching = mask.sum()
            if matching > 0:
                volumes[mask] += row['Volume'] / matching

        # POC
        poc_idx = np.argmax(volumes)
        poc = float(bin_centers[poc_idx])

        # Value Area (70% of volume)
        total_vol = volumes.sum()
        target = total_vol * 0.7
        sorted_idx = np.argsort(volumes)[::-1]
        cum = 0
        va_indices = []
        for i in sorted_idx:
            cum += volumes[i]
            va_indices.append(i)
            if cum >= target:
                break
        va_indices.sort()
        val = float(bin_centers[va_indices[0]])
        vah = float(bin_centers[va_indices[-1]])

        return {
            'poc': poc, 'vah': vah, 'val': val,
            'price': bin_centers.tolist(),
            'volume': volumes.tolist(),
        }

    def _find_confluences(self, tolerance_pct: float = 0.5) -> List[Dict]:
        """Find levels that align across multiple timeframes."""
        all_levels = []
        for tf, data in self.results.items():
            if 'error' in data:
                continue
            for level_type in ['poc', 'vah', 'val']:
                all_levels.append({
                    'price': data[level_type],
                    'type': level_type.upper(),
                    'timeframe': data['label'],
                    'tf_key': tf,
                })

        # Cluster nearby levels
        if not all_levels:
            return []

        levels_sorted = sorted(all_levels, key=lambda x: x['price'])
        clusters = []
        current_cluster = [levels_sorted[0]]

        for level in levels_sorted[1:]:
            ref_price = current_cluster[0]['price']
            if abs(level['price'] - ref_price) / ref_price * 100 <= tolerance_pct:
                current_cluster.append(level)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [level]

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        # Format confluences
        confluences = []
        for cluster in clusters:
            avg_price = np.mean([l['price'] for l in cluster])
            types = [f"{l['type']} ({l['timeframe']})" for l in cluster]
            timeframes_involved = list(set(l['tf_key'] for l in cluster))

            confluences.append({
                'price': round(avg_price, 2),
                'levels': types,
                'strength': len(cluster),
                'timeframes': len(timeframes_involved),
                'description': ' + '.join(types),
            })

        return sorted(confluences, key=lambda x: x['strength'], reverse=True)

    def _rank_levels(self, confluences: List[Dict]) -> List[Dict]:
        """Rank confluence levels by strength."""
        ranked = []
        for c in confluences:
            score = c['strength'] * 2 + c['timeframes'] * 3
            strength_label = 'EXTREME' if score >= 10 else 'STRONG' if score >= 6 else 'MODERATE'
            ranked.append({
                'price': c['price'],
                'score': score,
                'strength': strength_label,
                'description': c['description'],
            })
        return sorted(ranked, key=lambda x: x['score'], reverse=True)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    mtf = MultiTimeframeAnalyzer('SPY', ['15m', '1h', '1d'])
    result = mtf.analyze()
    for tf, data in result['timeframes'].items():
        if 'error' not in data:
            print(f"{data['label']}: POC={data['poc']:.2f} VAH={data['vah']:.2f} VAL={data['val']:.2f}")
    print(f"\nConfluences: {len(result['confluences'])}")
    for c in result['confluences']:
        print(f"  ${c['price']:.2f} (strength {c['strength']}): {c['description']}")
