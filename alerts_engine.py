"""
Alerts Engine
Monitor price levels, VP signals, and patterns.
Stores alerts in Streamlit session state and JSON file.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


ALERTS_FILE = os.path.join(os.path.dirname(__file__), '.alerts.json')


class AlertsEngine:
    """Manage trading alerts."""

    def __init__(self):
        self.alerts = self._load_alerts()

    def add_alert(self, ticker: str, alert_type: str, condition: str,
                  price: float, note: str = '') -> Dict:
        """Add a new alert."""
        alert = {
            'id': len(self.alerts) + 1,
            'ticker': ticker.upper(),
            'type': alert_type,  # 'PRICE_ABOVE', 'PRICE_BELOW', 'POC_TOUCH', 'VAH_BREAK', 'VAL_BREAK'
            'condition': condition,
            'price': price,
            'note': note,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'triggered': False,
            'triggered_at': None,
            'active': True,
        }
        self.alerts.append(alert)
        self._save_alerts()
        return alert

    def check_alerts(self, ticker: str, current_price: float,
                     poc: float = 0, vah: float = 0, val: float = 0) -> List[Dict]:
        """Check which alerts are triggered."""
        triggered = []
        for alert in self.alerts:
            if not alert['active'] or alert['triggered']:
                continue
            if alert['ticker'] != ticker.upper():
                continue

            fired = False
            if alert['type'] == 'PRICE_ABOVE' and current_price >= alert['price']:
                fired = True
            elif alert['type'] == 'PRICE_BELOW' and current_price <= alert['price']:
                fired = True
            elif alert['type'] == 'POC_TOUCH' and poc > 0:
                if abs(current_price - poc) / poc * 100 < 0.1:
                    fired = True
            elif alert['type'] == 'VAH_BREAK' and vah > 0:
                if current_price > vah:
                    fired = True
            elif alert['type'] == 'VAL_BREAK' and val > 0:
                if current_price < val:
                    fired = True

            if fired:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                triggered.append(alert)

        if triggered:
            self._save_alerts()
        return triggered

    def get_active_alerts(self, ticker: Optional[str] = None) -> List[Dict]:
        """Get all active alerts."""
        alerts = [a for a in self.alerts if a['active'] and not a['triggered']]
        if ticker:
            alerts = [a for a in alerts if a['ticker'] == ticker.upper()]
        return alerts

    def get_triggered_alerts(self, ticker: Optional[str] = None) -> List[Dict]:
        """Get recently triggered alerts."""
        alerts = [a for a in self.alerts if a['triggered']]
        if ticker:
            alerts = [a for a in alerts if a['ticker'] == ticker.upper()]
        return alerts[-10:]  # Last 10

    def delete_alert(self, alert_id: int):
        """Delete an alert by ID."""
        self.alerts = [a for a in self.alerts if a['id'] != alert_id]
        self._save_alerts()

    def clear_triggered(self):
        """Clear all triggered alerts."""
        self.alerts = [a for a in self.alerts if not a['triggered']]
        self._save_alerts()

    def _save_alerts(self):
        """Save alerts to JSON file."""
        try:
            with open(ALERTS_FILE, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        except Exception:
            pass

    def _load_alerts(self) -> List[Dict]:
        """Load alerts from JSON file."""
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []


class WatchlistManager:
    """Manage custom watchlists saved to JSON."""

    WATCHLISTS_FILE = os.path.join(os.path.dirname(__file__), '.watchlists.json')

    DEFAULT_WATCHLISTS = {
        'US Indices': ['SPY', 'QQQ', 'DIA', 'IWM'],
        'Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
        'Commodities': ['GC=F', 'SI=F', 'CL=F'],
        'Crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD'],
        'Forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'],
    }

    def __init__(self):
        self.watchlists = self._load()

    def get_all(self) -> Dict[str, List[str]]:
        """Get all watchlists."""
        return self.watchlists

    def get_names(self) -> List[str]:
        """Get watchlist names."""
        return list(self.watchlists.keys())

    def get_tickers(self, name: str) -> List[str]:
        """Get tickers for a watchlist."""
        return self.watchlists.get(name, [])

    def create(self, name: str, tickers: List[str]):
        """Create or update a watchlist."""
        self.watchlists[name] = [t.upper().strip() for t in tickers if t.strip()]
        self._save()

    def delete(self, name: str):
        """Delete a watchlist."""
        if name in self.watchlists:
            del self.watchlists[name]
            self._save()

    def add_ticker(self, name: str, ticker: str):
        """Add a ticker to a watchlist."""
        if name not in self.watchlists:
            self.watchlists[name] = []
        t = ticker.upper().strip()
        if t not in self.watchlists[name]:
            self.watchlists[name].append(t)
            self._save()

    def remove_ticker(self, name: str, ticker: str):
        """Remove a ticker from a watchlist."""
        if name in self.watchlists:
            t = ticker.upper().strip()
            self.watchlists[name] = [x for x in self.watchlists[name] if x != t]
            self._save()

    def _save(self):
        try:
            with open(self.WATCHLISTS_FILE, 'w') as f:
                json.dump(self.watchlists, f, indent=2)
        except Exception:
            pass

    def _load(self) -> Dict[str, List[str]]:
        try:
            if os.path.exists(self.WATCHLISTS_FILE):
                with open(self.WATCHLISTS_FILE, 'r') as f:
                    data = json.load(f)
                    if data:
                        return data
        except Exception:
            pass
        return dict(self.DEFAULT_WATCHLISTS)


if __name__ == "__main__":
    # Test alerts
    engine = AlertsEngine()
    engine.add_alert('SPY', 'PRICE_ABOVE', 'SPY above 700', 700)
    engine.add_alert('SPY', 'PRICE_BELOW', 'SPY below 650', 650)
    print(f"Active alerts: {len(engine.get_active_alerts())}")

    triggered = engine.check_alerts('SPY', 680, poc=682, vah=690, val=678)
    print(f"Triggered: {len(triggered)}")

    # Test watchlists
    wm = WatchlistManager()
    print(f"\nWatchlists: {wm.get_names()}")
    for name in wm.get_names():
        print(f"  {name}: {wm.get_tickers(name)}")
