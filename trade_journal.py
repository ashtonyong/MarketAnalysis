"""
Trade Journal & Notes Manager
Log trades, track performance, save per-ticker notes.
All data persisted locally in JSON files.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


JOURNAL_FILE = os.path.join(os.path.dirname(__file__), '.trade_journal.json')
NOTES_FILE = os.path.join(os.path.dirname(__file__), '.ticker_notes.json')
PREFS_FILE = os.path.join(os.path.dirname(__file__), '.user_prefs.json')


class TradeJournal:
    """Log and track trades with P&L analytics."""

    def __init__(self):
        self.trades = self._load()

    def add_trade(self, ticker: str, direction: str, entry_price: float,
                  exit_price: float, size: float, entry_date: str = '',
                  exit_date: str = '', strategy: str = '', notes: str = '') -> Dict:
        """Add a completed trade."""
        pnl = (exit_price - entry_price) * size if direction == 'LONG' else (entry_price - exit_price) * size
        pnl_pct = ((exit_price - entry_price) / entry_price * 100) if direction == 'LONG' else ((entry_price - exit_price) / entry_price * 100)

        trade = {
            'id': len(self.trades) + 1,
            'ticker': ticker.upper(),
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'size': size,
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'result': 'WIN' if pnl > 0 else 'LOSS' if pnl < 0 else 'BREAKEVEN',
            'entry_date': entry_date or datetime.now().strftime('%Y-%m-%d'),
            'exit_date': exit_date or datetime.now().strftime('%Y-%m-%d'),
            'strategy': strategy,
            'notes': notes,
            'logged_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        self.trades.append(trade)
        self._save()
        return trade

    def get_all_trades(self) -> List[Dict]:
        """Get all trades."""
        return self.trades

    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.trades:
            return {
                'total_trades': 0, 'wins': 0, 'losses': 0,
                'win_rate': 0, 'total_pnl': 0, 'avg_pnl': 0,
                'best_trade': 0, 'worst_trade': 0,
                'avg_winner': 0, 'avg_loser': 0,
                'profit_factor': 0, 'equity_curve': [],
            }

        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] < 0]
        pnls = [t['pnl'] for t in self.trades]

        total_wins = sum(t['pnl'] for t in wins) if wins else 0
        total_losses = abs(sum(t['pnl'] for t in losses)) if losses else 0

        # Equity curve
        equity = []
        running = 0
        for t in self.trades:
            running += t['pnl']
            equity.append({'date': t['exit_date'], 'equity': round(running, 2)})

        return {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(len(wins) / len(self.trades) * 100, 1) if self.trades else 0,
            'total_pnl': round(sum(pnls), 2),
            'avg_pnl': round(sum(pnls) / len(pnls), 2) if pnls else 0,
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
            'avg_winner': round(total_wins / len(wins), 2) if wins else 0,
            'avg_loser': round(-total_losses / len(losses), 2) if losses else 0,
            'profit_factor': round(total_wins / total_losses, 2) if total_losses > 0 else 0,
            'equity_curve': equity,
        }

    def delete_trade(self, trade_id: int):
        """Delete a trade by ID."""
        self.trades = [t for t in self.trades if t['id'] != trade_id]
        self._save()

    def clear_all(self):
        """Clear all trades."""
        self.trades = []
        self._save()

    def export_csv(self) -> str:
        """Export trades as CSV string."""
        if not self.trades:
            return "No trades to export"
        headers = ['id', 'ticker', 'direction', 'entry_price', 'exit_price',
                    'size', 'pnl', 'pnl_pct', 'result', 'entry_date',
                    'exit_date', 'strategy', 'notes']
        lines = [','.join(headers)]
        for t in self.trades:
            row = [str(t.get(h, '')) for h in headers]
            lines.append(','.join(row))
        return '\n'.join(lines)

    def _save(self):
        try:
            with open(JOURNAL_FILE, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception:
            pass

    def _load(self) -> List[Dict]:
        try:
            if os.path.exists(JOURNAL_FILE):
                with open(JOURNAL_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []


class TickerNotes:
    """Save personal notes per ticker."""

    def __init__(self):
        self.notes = self._load()

    def get_note(self, ticker: str) -> str:
        """Get note for a ticker."""
        return self.notes.get(ticker.upper(), '')

    def save_note(self, ticker: str, note: str):
        """Save a note for a ticker."""
        self.notes[ticker.upper()] = note
        self._save()

    def delete_note(self, ticker: str):
        """Delete a note."""
        if ticker.upper() in self.notes:
            del self.notes[ticker.upper()]
            self._save()

    def get_all(self) -> Dict[str, str]:
        """Get all notes."""
        return self.notes

    def _save(self):
        try:
            with open(NOTES_FILE, 'w') as f:
                json.dump(self.notes, f, indent=2)
        except Exception:
            pass

    def _load(self) -> Dict[str, str]:
        try:
            if os.path.exists(NOTES_FILE):
                with open(NOTES_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}


class UserPreferences:
    """Manage user preferences."""

    DEFAULTS = {
        'default_ticker': 'SPY',
        'default_period': '1mo',
        'default_interval': '15m',
        'auto_refresh': False,
        'refresh_rate': 10,
        'theme': 'dark',
    }

    def __init__(self):
        self.prefs = self._load()

    def get(self, key: str, default=None):
        return self.prefs.get(key, self.DEFAULTS.get(key, default))

    def set(self, key: str, value):
        self.prefs[key] = value
        self._save()

    def get_all(self) -> Dict:
        merged = dict(self.DEFAULTS)
        merged.update(self.prefs)
        return merged

    def save_all(self, prefs: Dict):
        self.prefs.update(prefs)
        self._save()

    def _save(self):
        try:
            with open(PREFS_FILE, 'w') as f:
                json.dump(self.prefs, f, indent=2)
        except Exception:
            pass

    def _load(self) -> Dict:
        try:
            if os.path.exists(PREFS_FILE):
                with open(PREFS_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}


if __name__ == "__main__":
    # Test journal
    j = TradeJournal()
    j.add_trade('SPY', 'LONG', 680, 690, 100, strategy='VP Bounce')
    j.add_trade('QQQ', 'SHORT', 520, 510, 50, strategy='POC Rejection')
    stats = j.get_stats()
    print(f"Trades: {stats['total_trades']}, Win Rate: {stats['win_rate']}%")
    print(f"Total P&L: ${stats['total_pnl']}, Best: ${stats['best_trade']}")
    print(f"Profit Factor: {stats['profit_factor']}")

    # Test notes
    n = TickerNotes()
    n.save_note('SPY', 'Watch for POC bounce at 682')
    print(f"\nSPY Note: {n.get_note('SPY')}")

    # Test prefs
    p = UserPreferences()
    print(f"\nDefault ticker: {p.get('default_ticker')}")
