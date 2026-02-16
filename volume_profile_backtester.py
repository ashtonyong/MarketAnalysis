"""
Volume Profile Backtester
Simulates trading strategies based on Volume Profile analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Callable
from volume_profile_engine import VolumeProfileEngine

class VolumeProfileBacktester:
    """
    Backtesting Engine for Volume Profile Strategies.
    """
    
    def __init__(self, ticker: str, start_date: str = None, end_date: str = None, initial_capital: float = 10000.0):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.engine = VolumeProfileEngine(ticker, period="1y", interval="1d") # Fetch enough data
        self.trades = []
        self.equity_curve = []
        self.data = pd.DataFrame()

    def load_data(self):
        """Fetches and prepares data for backtesting."""
        print(f"Fetching data for {self.ticker}...")
        # For backtesting, we might want a longer period. 
        # Note: yfinance limitations might apply for intraday data over long periods.
        # We'll default to Daily bars for simpler, faster backtesting initially.
        self.data = self.engine.fetch_data()
        
        # Filter by date if specified (and if data has index)
        if hasattr(self.data.index, 'tz_localize'):
             # Normalize timezone if needed, typically yfinance returns tz-aware
             pass

    def run_strategy(self, strategy_func: Callable[[pd.DataFrame, pd.DataFrame, int], dict]):
        """
        Runs a strategy over the historical data.
        
        Args:
            strategy_func: Function that takes (current_bar, history, position) and returns action signal.
                           Signal dict: {'action': 'buy'|'sell'|'hold', 'stop_loss': float, 'take_profit': float}
        """
        if self.data.empty:
            self.load_data()
            
        print("Running backtest simulation...")
        
        position = 0 # 0: Flat, 1: Long, -1: Short
        entry_price = 0.0
        stop_loss = 0.0
        take_profit = 0.0
        
        self.equity_curve = [self.initial_capital]
        self.trades = []
        
        # Iterating bar by bar (simulating real-time)
        # We need a "Lookback" for the profile. 
        # Strategy: Re-calculate profile every day based on last N days? 
        # Or use a rolling window?
        # For efficiency, we will assume a "Rolling 20-day Profile" is used for decision making.
        
        profile_window = 20 # days
        
        for i in range(profile_window, len(self.data)):
            current_bar = self.data.iloc[i]
            # Data available up to yesterday for profile calc
            history = self.data.iloc[i-profile_window:i] 
            
            # --- SIMPLIFIED: Re-calculating profile every step is SLOW. 
            # Optimization: Calculate key levels (POC, VAH, VAL) on rolling basis or skip-steps.
            # For now, we will do it every step to be accurate to the "Agent" behavior.
            
            # Create a temporary engine context for this history slice
            # We can't reuse self.engine nicely because it holds full state.
            # We'll calculate profile manually on the slice using the engine's static-like method if possible,
            # or just instantiate a new one (slow but safe).
            
            # Optimization: Only calc profile if we are looking for entry.
            # If in trade, we manage trade.
            
            # 1. Manage current position (Exit checks)
            current_date = self.data.index[i]
            current_close = current_bar['Close']
            current_high = current_bar['High']
            current_low = current_bar['Low']
            
            pnl = 0
            trade_action = None
            
            if position == 1: # Long
                # Check stops/targets (assuming hit on High/Low)
                if current_low <= stop_loss:
                    trade_action = "EXIT_STOP"
                    exit_price = stop_loss # Slippage not modeled
                elif current_high >= take_profit:
                    trade_action = "EXIT_TARGET"
                    exit_price = take_profit
                    
                if trade_action:
                    pnl = (exit_price - entry_price) * (self.capital / entry_price) # Full capital compounding
                    self.capital = self.capital * (exit_price / entry_price)
                    position = 0
                    self.trades.append({
                        'entry_date': entry_date, 
                        'exit_date': current_date,
                        'type': 'Long',
                        'entry': entry_price,
                        'exit': exit_price,
                        'reason': trade_action,
                        'pnl_pct': (exit_price - entry_price)/entry_price
                    })

            elif position == -1: # Short
                if current_high >= stop_loss:
                    trade_action = "EXIT_STOP"
                    exit_price = stop_loss
                elif current_low <= take_profit:
                    trade_action = "EXIT_TARGET"
                    exit_price = take_profit
                    
                if trade_action:
                    # Short PnL: (Entry - Exit) / Entry
                    # New Capital = Old Capital * (1 + PnL)
                    raw_pnl_pct = (entry_price - exit_price) / entry_price
                    self.capital = self.capital * (1 + raw_pnl_pct)
                    position = 0
                    self.trades.append({
                        'entry_date': entry_date, 
                        'exit_date': current_date,
                        'type': 'Short',
                        'entry': entry_price,
                        'exit': exit_price,
                        'reason': trade_action,
                        'pnl_pct': raw_pnl_pct 
                    })

            # 2. Look for Entry (if flat)
            if position == 0:
                # We need profile levels for the strategy
                # Calculate on history
                # We use engine.calculate_volume_profile(history)
                # But we can't easily access it without modifying engine to accept DF arg in all methods.
                # Let's fix engine to be more flexible or just use helper here.
                
                # Assume engine has correct method from previous refactor
                profile = self.engine.calculate_volume_profile(history)
                poc = self.engine.find_poc(profile)
                val, vah = self.engine.find_value_area(profile)
                
                levels = {'poc': poc, 'val': val, 'vah': vah, 'close': history['Close'].iloc[-1]}
                
                signal = strategy_func(current_bar, levels, position)
                
                if signal['action'] == 'buy':
                    position = 1
                    entry_price = current_close # Simulate entering at Close
                    entry_date = current_date
                    stop_loss = signal['stop_loss']
                    take_profit = signal['take_profit']
                elif signal['action'] == 'sell':
                    position = -1
                    entry_price = current_close
                    entry_date = current_date
                    stop_loss = signal['stop_loss']
                    take_profit = signal['take_profit']
            
            self.equity_curve.append(self.capital)
            
        return self.get_results()

    def get_results(self):
        """Calculates performance metrics."""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {"error": "No trades generated"}
            
        wins = [t for t in self.trades if t['pnl_pct'] > 0]
        losses = [t for t in self.trades if t['pnl_pct'] <= 0]
        
        win_rate = len(wins) / total_trades * 100
        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) * 100 if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) * 100 if losses else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_return": round(total_return, 2),
            "final_capital": round(self.capital, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2)
        }


# --- Strategies ---

def strategy_mean_reversion(bar, levels, position):
    """
    Mean Reversion Strategy:
    - If price opened below VAL and closes inside Value Area -> Buy (Reclaiming Value)
    - If price opened above VAH and closes inside Value Area -> Sell (Failed Breakout)
    """
    open_price = bar['Open']
    close_price = bar['Close']
    val = levels['val']
    vah = levels['vah']
    poc = levels['poc']
    
    # Buy Rule: Reclaim VAL
    if open_price < val and close_price > val:
        return {
            'action': 'buy',
            'stop_loss': close_price * 0.98, # 2% SL
            'take_profit': poc # Target POC
        }
    
    # Sell Rule: Fail VAH
    if open_price > vah and close_price < vah:
        return {
            'action': 'sell',
            'stop_loss': close_price * 1.02, # 2% SL
            'take_profit': poc # Target POC
        }
        
    return {'action': 'hold'}

def strategy_trend_following(bar, levels, position):
    """
    Trend Following Strategy:
    - If price closes above VAH -> Buy (Breakout)
    - If price closes below VAL -> Sell (Breakdown)
    """
    close_price = bar['Close']
    val = levels['val']
    vah = levels['vah']
    
    # Buy Rule: Breakout VAH
    if close_price > vah:
         return {
            'action': 'buy',
            'stop_loss': val, # Wide stop at VAL
            'take_profit': close_price + (vah - val) # 1:1 Range extension
        }
    
    # Sell Rule: Breakdown VAL
    if close_price < val:
         return {
            'action': 'sell',
            'stop_loss': vah,
            'take_profit': close_price - (vah - val)
        }
        
    return {'action': 'hold'}

STRATEGIES = {
    'mean_reversion': strategy_mean_reversion,
    'trend_following': strategy_trend_following
}


if __name__ == "__main__":
    # Test Backtester
    bt = VolumeProfileBacktester("SPY", initial_capital=10000)
    print("Testing Mean Reversion Strategy...")
    results = bt.run_strategy(strategy_mean_reversion)
    print(results)
