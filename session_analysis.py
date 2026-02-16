"""
Session Analysis
Splits intraday data into Asia, London, and NY sessions.
Calculates volume profile metrics for each session.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from volume_profile_engine import VolumeProfileEngine


# Session time ranges in US Eastern Time (ET)
# These are approximate ranges for futures/forex-style sessions
SESSIONS = {
    'Asia': {'start': '19:00', 'end': '02:00'},    # 7pm-2am ET (prev day evening)
    'London': {'start': '03:00', 'end': '09:30'},   # 3am-9:30am ET
    'NY': {'start': '09:30', 'end': '16:00'},        # 9:30am-4pm ET (Regular Trading Hours)
}


class SessionAnalyzer:
    """
    Splits intraday price data into trading sessions and computes
    volume profile metrics for each.
    """

    def __init__(self, ticker: str, period: str = "5d", interval: str = "5m"):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data: Optional[pd.DataFrame] = None
        self.session_results: Dict = {}

    def _fetch_data(self) -> pd.DataFrame:
        """Fetch intraday data."""
        engine = VolumeProfileEngine(self.ticker, self.period, self.interval)
        self.data = engine.fetch_data()
        return self.data

    def _filter_session(self, data: pd.DataFrame, session_name: str) -> pd.DataFrame:
        """Filter dataframe rows to a specific session time window."""
        session = SESSIONS[session_name]
        start_h, start_m = map(int, session['start'].split(':'))
        end_h, end_m = map(int, session['end'].split(':'))

        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        # Convert index to ET if not already
        idx = data.index
        if hasattr(idx, 'tz'):
            try:
                idx = idx.tz_convert('US/Eastern')
            except Exception:
                pass

        time_minutes = idx.hour * 60 + idx.minute

        if start_minutes <= end_minutes:
            # Normal range (e.g., 09:30 to 16:00)
            mask = (time_minutes >= start_minutes) & (time_minutes < end_minutes)
        else:
            # Overnight range (e.g., 19:00 to 02:00)
            mask = (time_minutes >= start_minutes) | (time_minutes < end_minutes)

        return data[mask]

    def analyze_sessions(self) -> Dict:
        """
        Analyze each session and return POC/VAH/VAL/volume for each.
        """
        if self.data is None or self.data.empty:
            self._fetch_data()

        if self.data is None or self.data.empty:
            return {'error': 'No data available'}

        results = {}

        for session_name in SESSIONS:
            session_data = self._filter_session(self.data, session_name)

            if session_data.empty or len(session_data) < 3:
                results[session_name] = {
                    'status': 'NO_DATA',
                    'bars': 0,
                    'volume': 0
                }
                continue

            # Calculate profile for this session slice
            engine = VolumeProfileEngine(data=session_data)
            metrics = engine.get_all_metrics()

            results[session_name] = {
                'status': 'OK',
                'bars': len(session_data),
                'poc': round(metrics['poc'], 2),
                'vah': round(metrics['vah'], 2),
                'val': round(metrics['val'], 2),
                'volume': int(session_data['Volume'].sum()),
                'high': round(session_data['High'].max(), 2),
                'low': round(session_data['Low'].min(), 2),
                'range': round(session_data['High'].max() - session_data['Low'].min(), 2),
            }

        self.session_results = results
        return results

    def get_session_comparison(self) -> Dict:
        """
        Compare sessions: dominant session, POC shift, overnight gap.
        """
        if not self.session_results:
            self.analyze_sessions()

        sessions = self.session_results
        comparison = {}

        # Find dominant session by volume
        active_sessions = {
            k: v for k, v in sessions.items()
            if v.get('status') == 'OK'
        }

        if not active_sessions:
            return {'error': 'No active session data'}

        dominant = max(active_sessions, key=lambda k: active_sessions[k]['volume'])
        total_volume = sum(s['volume'] for s in active_sessions.values())

        comparison['dominant_session'] = dominant
        comparison['volume_breakdown'] = {}
        for name, data in active_sessions.items():
            pct = (data['volume'] / total_volume * 100) if total_volume > 0 else 0
            comparison['volume_breakdown'][name] = {
                'volume': data['volume'],
                'pct': round(pct, 1)
            }

        # POC shift across sessions
        pocs = {k: v['poc'] for k, v in active_sessions.items() if v.get('poc', 0) > 0}
        if len(pocs) >= 2:
            poc_values = list(pocs.values())
            poc_shift = ((poc_values[-1] - poc_values[0]) / poc_values[0]) * 100
            comparison['poc_shift_pct'] = round(poc_shift, 3)
            if poc_shift > 0.1:
                comparison['poc_direction'] = 'HIGHER'
            elif poc_shift < -0.1:
                comparison['poc_direction'] = 'LOWER'
            else:
                comparison['poc_direction'] = 'STABLE'
        else:
            comparison['poc_shift_pct'] = 0
            comparison['poc_direction'] = 'N/A'

        # Overnight gap (difference between Asia close and NY open, if available)
        if 'Asia' in active_sessions and 'NY' in active_sessions:
            asia_data = active_sessions['Asia']
            ny_data = active_sessions['NY']
            # Approximate gap using session ranges
            gap = ny_data['low'] - asia_data['high']  # Simplified
            comparison['overnight_gap'] = round(gap, 2)
            comparison['gap_type'] = 'GAP UP' if gap > 0 else 'GAP DOWN' if gap < 0 else 'FLAT'
        else:
            comparison['overnight_gap'] = 0
            comparison['gap_type'] = 'N/A'

        return comparison

    def generate_report(self) -> str:
        """Generate text report."""
        if not self.session_results:
            self.analyze_sessions()

        comparison = self.get_session_comparison()

        lines = [
            f"Session Analysis: {self.ticker}",
            "=" * 50,
        ]

        for name, data in self.session_results.items():
            if data.get('status') == 'OK':
                lines.append(f"\n{name.upper()} Session:")
                lines.append(f"  POC: ${data['poc']:.2f} | Range: ${data['low']:.2f}-${data['high']:.2f}")
                lines.append(f"  Volume: {data['volume']:,} | Bars: {data['bars']}")
            else:
                lines.append(f"\n{name.upper()} Session: No data")

        lines.append(f"\n{'='*50}")
        lines.append(f"Dominant: {comparison.get('dominant_session', 'N/A')}")
        lines.append(f"POC Direction: {comparison.get('poc_direction', 'N/A')} "
                      f"({comparison.get('poc_shift_pct', 0):.3f}%)")
        lines.append(f"Overnight Gap: {comparison.get('gap_type', 'N/A')} "
                      f"(${comparison.get('overnight_gap', 0):.2f})")

        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"

    analyzer = SessionAnalyzer(ticker)
    print(analyzer.generate_report())
