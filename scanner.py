"""
Multi-Asset Volume Profile Scanner
Scans multiple tickers in parallel and ranks by opportunity score.
"""

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from datetime import datetime
from volume_profile_engine import VolumeProfileEngine


# Default watchlists
WATCHLISTS = {
    'sp500_top20': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
        'JPM', 'V', 'UNH', 'MA', 'HD', 'PG', 'JNJ', 'COST', 'ABBV',
        'CRM', 'AVGO', 'MRK'
    ],
    'tech': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        'CRM', 'AVGO', 'AMD', 'INTC', 'ORCL', 'ADBE', 'NFLX', 'QCOM'
    ],
    'etfs': [
        'SPY', 'QQQ', 'DIA', 'IWM', 'XLF', 'XLE', 'XLK', 'XLV',
        'XLI', 'XLP', 'ARKK', 'GLD', 'SLV', 'TLT', 'VXX'
    ],
    'mega_caps': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'
    ],
    'quick_test': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA']
}


class VolumeProfileScanner:
    """
    Scans multiple tickers for volume profile opportunities.
    Uses parallel execution for speed.
    """

    def __init__(self, tickers: List[str], period: str = "1mo",
                 interval: str = "1d", max_workers: int = 5):
        self.tickers = [t.upper() for t in tickers]
        self.period = period
        self.interval = interval
        self.max_workers = max_workers
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
        self.scan_time: Optional[str] = None

    def _scan_single(self, ticker: str) -> Dict:
        """Analyze a single ticker. Returns dict with metrics + score."""
        try:
            engine = VolumeProfileEngine(ticker, self.period, self.interval)
            metrics = engine.get_all_metrics()

            if not metrics or metrics.get('poc', 0) == 0:
                return {'ticker': ticker, 'error': 'No data'}

            score = self._calculate_score(metrics)

            return {
                'ticker': ticker,
                'current_price': round(metrics['current_price'], 2),
                'poc': round(metrics['poc'], 2),
                'vah': round(metrics['vah'], 2),
                'val': round(metrics['val'], 2),
                'position': metrics['position'],
                'distance_from_poc_pct': round(abs(metrics['distance_from_poc_pct']), 2),
                'opportunity_score': score,
                'signal': self._get_signal(metrics, score),
                'error': None
            }
        except Exception as e:
            return {'ticker': ticker, 'error': str(e)}

    def _calculate_score(self, metrics: Dict) -> int:
        """Score 0-100 based on proximity to key levels and position."""
        score = 50
        distance = abs(metrics.get('distance_from_poc_pct', 0))

        # Proximity to POC
        if distance < 1:
            score += 35
        elif distance < 2:
            score += 25
        elif distance < 5:
            score += 10
        else:
            score -= 10

        # Position context
        position = metrics.get('position', '')
        if 'ABOVE' in position and distance < 3:
            score += 10  # Near breakout confirmation
        elif 'BELOW' in position and distance < 3:
            score += 10  # Potential reversal
        elif 'INSIDE' in position:
            score += 5

        # Penalize overextended
        if distance > 10:
            score -= 20

        return max(0, min(100, score))

    def _get_signal(self, metrics: Dict, score: int) -> str:
        """Generate human-readable signal."""
        position = metrics.get('position', '')
        distance = abs(metrics.get('distance_from_poc_pct', 0))

        if score >= 80:
            if 'ABOVE' in position:
                return "[!!] Strong setup: Near POC from above"
            elif 'BELOW' in position:
                return "[!!] Strong setup: Near POC from below"
            else:
                return "[!!] Strong setup: Tight in value area"
        elif score >= 60:
            return "[!] Moderate opportunity"
        elif score >= 40:
            return "[-] Neutral -- wait for setup"
        else:
            return "[x] Weak -- overextended"

    def scan_all(self) -> List[Dict]:
        """Scan all tickers in parallel. Returns sorted results."""
        self.results = []
        self.errors = []
        self.scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._scan_single, ticker): ticker
                for ticker in self.tickers
            }

            for future in as_completed(futures):
                result = future.result()
                if result.get('error'):
                    self.errors.append(result)
                else:
                    self.results.append(result)

        # Sort by opportunity score descending
        self.results.sort(key=lambda x: x['opportunity_score'], reverse=True)
        return self.results

    def get_top(self, n: int = 5) -> List[Dict]:
        """Get top N opportunities."""
        if not self.results:
            self.scan_all()
        return self.results[:n]

    def generate_report(self) -> str:
        """Generate a text report of scan results."""
        if not self.results:
            self.scan_all()

        lines = [
            f"Volume Profile Scanner Report",
            f"Scan Time: {self.scan_time}",
            f"Tickers Scanned: {len(self.results) + len(self.errors)}",
            f"Successful: {len(self.results)} | Errors: {len(self.errors)}",
            "",
            "=" * 60,
            "TOP OPPORTUNITIES",
            "=" * 60,
        ]

        for i, r in enumerate(self.results[:10], 1):
            lines.append(
                f"{i:>2}. {r['ticker']:<6} | Score: {r['opportunity_score']:>3}/100 | "
                f"${r['current_price']:>8.2f} | {r['position']:<15} | {r['signal']}"
            )

        if self.errors:
            lines.append("")
            lines.append(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"   {e['ticker']}: {e['error']}")

        return "\n".join(lines)

    def export_csv(self, filepath: str = None) -> str:
        """Export scan results to CSV."""
        if not self.results:
            self.scan_all()

        if filepath is None:
            filepath = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        df = pd.DataFrame(self.results)
        df.to_csv(filepath, index=False)
        return filepath

    def to_dataframe(self) -> pd.DataFrame:
        """Return results as a pandas DataFrame."""
        if not self.results:
            self.scan_all()
        return pd.DataFrame(self.results)


if __name__ == "__main__":
    import sys

    # Default to quick_test watchlist
    tickers = WATCHLISTS.get(sys.argv[1], WATCHLISTS['quick_test']) if len(sys.argv) > 1 else WATCHLISTS['quick_test']

    print(f"Scanning {len(tickers)} tickers...")
    scanner = VolumeProfileScanner(tickers)
    scanner.scan_all()
    print(scanner.generate_report())
