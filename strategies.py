
import pandas as pd
import numpy as np
from datetime import datetime
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, name, engine=None):
        self.name = name
        self.engine = engine
        self.trades = []
        self.equity_curve = []
        self.current_position = None  # {ticker, entry, size, risk_per_share}

    def set_engine(self, engine):
        self.engine = engine

    @abstractmethod
    def run(self, df, profile_data, capital=10000, risk_pct=0.01):
        """Standard interface for executing strategy logic."""
        pass

    def calculate_position_size(self, capital, risk_pct, entry, stop_loss):
        if entry == stop_loss: return 0
        risk_per_share = abs(entry - stop_loss)
        total_risk = capital * risk_pct
        shares = int(total_risk / risk_per_share)
        return shares

    def log_trade(self, ticker, entry_time, exit_time, entry, exit, size, direction, reason):
        pnl = (exit - entry) * size if direction == "LONG" else (entry - exit) * size
        pnl_pct = (pnl / (entry * size)) * 100
        result = "WIN" if pnl > 0 else "LOSS"
        
        trade = {
            "Ticker": ticker,
            "Strategy": self.name,
            "Direction": direction,
            "Entry Time": entry_time,
            "Exit Time": exit_time,
            "Entry Price": entry,
            "Exit Price": exit,
            "Size": size,
            "P&L": pnl,
            "P&L %": pnl_pct,
            "Result": result,
            "Reason": reason
        }
        self.trades.append(trade)
        return pnl

class ValueAreaReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Value Area Reversion")

    def run(self, df, profile_data, capital=10000, risk_pct=0.01):
        """
        Logic: Use VA Low and VA High as reversion bands.
        If price opens outside VA and closes inside, target POC.
        Stop loss outside the VA edge.
        """
        self.trades = []
        equity = capital
        self.equity_curve = [{"Date": df.index[0], "Equity": equity}]
        
        vah = profile_data['vah']
        val = profile_data['val']
        poc = profile_data['poc']
        
        in_position = False
        entry_price = 0
        stop_loss = 0
        size = 0
        direction = ""
        entry_time = None

        for i in range(1, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            price = curr['Close']
            
            if notin_position:
                # Long Setup: Price was below VAL, now closes above VAL
                if prev['Close'] < val and curr['Close'] > val:
                    direction = "LONG"
                    entry_price = curr['Close']
                    stop_loss = val * 0.995 # 0.5% below VAL
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name
                
                # Short Setup: Price was above VAH, now closes below VAH
                elif prev['Close'] > vah and curr['Close'] < vah:
                    direction = "SHORT"
                    entry_price = curr['Close']
                    stop_loss = vah * 1.005 # 0.5% above VAH
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name

            elif in_position:
                # Exit Logic
                hit_stop = (direction == "LONG" and price <= stop_loss) or \
                           (direction == "SHORT" and price >= stop_loss)
                
                hit_target = (direction == "LONG" and price >= poc) or \
                             (direction == "SHORT" and price <= poc)
                
                if hit_stop or hit_target:
                    reason = "Target Hit" if hit_target else "Stop Loss"
                    pnl = self.log_trade("BACKTEST", entry_time, curr.name, entry_price, price, size, direction, reason)
                    equity += pnl
                    self.equity_curve.append({"Date": curr.name, "Equity": equity})
                    in_position = False

        return pd.DataFrame(self.trades), self.equity_curve


class POCBounceStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("POC Bounce")

    def run(self, df, profile_data, capital=10000, risk_pct=0.01):
        """
        Logic: Trade bounces off the Point of Control (POC).
        Entry: Price touches POC zone (+/- 0.1%) then closes away from it.
        Direction: Fade the move (Mean reversion from POC? No, POC is value).
        Actually, POC often acts as support/resistance.
        If price approaches from above and bounces up, LONG.
        If price approaches from below and rejects down, SHORT.
        """
        self.trades = []
        equity = capital
        self.equity_curve = [{"Date": df.index[0], "Equity": equity}]
        
        poc = profile_data['poc']
        buffer = poc * 0.001 # 0.1% buffer
        
        in_position = False
        direction = ""
        entry_price = 0
        stop_loss = 0
        size = 0
        entry_time = None

        for i in range(1, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            price = curr['Close']
            
            if not in_position:
                # LONG: Price dipped into POC zone but closed above it
                if prev['Close'] > poc and prev['Low'] <= (poc + buffer) and curr['Close'] > (poc + buffer):
                    direction = "LONG"
                    entry_price = curr['Close']
                    stop_loss = poc - buffer * 2 # Stop slightly below POC
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name
                
                # SHORT: Price rallied into POC zone but closed below it
                elif prev['Close'] < poc and prev['High'] >= (poc - buffer) and curr['Close'] < (poc - buffer):
                    direction = "SHORT"
                    entry_price = curr['Close']
                    stop_loss = poc + buffer * 2 # Stop slightly above POC
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name

            elif in_position:
                # Exit at 2R or Stop
                risk = abs(entry_price - stop_loss)
                target = entry_price + (risk * 2) if direction == "LONG" else entry_price - (risk * 2)
                
                hit_stop = (direction == "LONG" and price <= stop_loss) or \
                           (direction == "SHORT" and price >= stop_loss)
                hit_target = (direction == "LONG" and price >= target) or \
                             (direction == "SHORT" and price <= target)
                
                if hit_stop or hit_target:
                    exit_price = stop_loss if hit_stop else target
                    pnl = self.log_trade("BACKTEST", entry_time, curr.name, entry_price, exit_price, size, direction, "Target" if hit_target else "Stop")
                    equity += pnl
                    self.equity_curve.append({"Date": curr.name, "Equity": equity})
                    in_position = False

        return pd.DataFrame(self.trades), self.equity_curve

class FailedAuctionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Failed Auction")

    def run(self, df, profile_data, capital=10000, risk_pct=0.01):
        """
        Logic: Specific for Failed Breakouts of VA High/Low.
        If price breaks VAH but closes back inside -> Failed Auction (Short).
        If price breaks VAL but closes back inside -> Failed Auction (Long).
        Target: POC.
        """
        self.trades = []
        equity = capital
        self.equity_curve = [{"Date": df.index[0], "Equity": equity}]
        
        vah = profile_data['vah']
        val = profile_data['val']
        poc = profile_data['poc']
        
        in_position = False
        direction = ""
        entry_price = 0
        stop_loss = 0
        size = 0
        entry_time = None

        for i in range(1, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            price = curr['Close']

            if not in_position:
                # Failed Breakout Above VAH -> SHORT
                if prev['High'] > vah and curr['Close'] < vah and prev['Close'] > vah:
                    direction = "SHORT"
                    entry_price = curr['Close']
                    stop_loss = prev['High'] # Stop at the failed high
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name

                # Failed Breakout Below VAL -> LONG
                elif prev['Low'] < val and curr['Close'] > val and prev['Close'] < val:
                    direction = "LONG"
                    entry_price = curr['Close']
                    stop_loss = prev['Low'] # Stop at the failed low
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name

            elif in_position:
                hit_stop = (direction == "LONG" and price <= stop_loss) or \
                           (direction == "SHORT" and price >= stop_loss)
                hit_target = (direction == "LONG" and price >= poc) or \
                             (direction == "SHORT" and price <= poc)
                
                if hit_stop or hit_target:
                    exit_price = stop_loss if hit_stop else poc
                    pnl = self.log_trade("BACKTEST", entry_time, curr.name, entry_price, exit_price, size, direction, "Target" if hit_target else "Stop")
                    equity += pnl
                    self.equity_curve.append({"Date": curr.name, "Equity": equity})
                    in_position = False

        return pd.DataFrame(self.trades), self.equity_curve

class ZScoreMeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Z-Score Mean Reversion")

    def run(self, df, profile_data, capital=10000, risk_pct=0.01):
        """
        Logic: Calculate Z-Score of price relative to 20-period SMA.
        If Z-Score > 2 (Overbought) -> Short.
        If Z-Score < -2 (Oversold) -> Long.
        Exit when Z-Score returns to 0.
        """
        self.trades = []
        equity = capital
        self.equity_curve = [{"Date": df.index[0], "Equity": equity}]
        
        # Calculate stats
        window = 20
        df['SMA'] = df['Close'].rolling(window=window).mean()
        df['STD'] = df['Close'].rolling(window=window).std()
        df['ZScore'] = (df['Close'] - df['SMA']) / df['STD']
        
        in_position = False
        direction = ""
        entry_price = 0
        size = 0
        entry_time = None

        for i in range(window, len(df)):
            curr = df.iloc[i]
            z = curr['ZScore']
            price = curr['Close']
            
            if not in_position:
                if z < -2.0:
                    direction = "LONG"
                    entry_price = price
                    stop_loss = price * 0.98 # 2% stop
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name
                
                elif z > 2.0:
                    direction = "SHORT"
                    entry_price = price
                    stop_loss = price * 1.02 # 2% stop
                    size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                    if size > 0:
                        in_position = True
                        entry_time = curr.name

            elif in_position:
                # Exit when Z-Score crosses 0 or stop hit
                hit_stop = (direction == "LONG" and price <= stop_loss) or \
                           (direction == "SHORT" and price >= stop_loss)
                
                reverted = (direction == "LONG" and z >= 0) or \
                           (direction == "SHORT" and z <= 0)
                
                if hit_stop or reverted:
                    exit_price = stop_loss if hit_stop else price
                    reason = "Mean Reversion" if reverted else "Stop Loss"
                    pnl = self.log_trade("BACKTEST", entry_time, curr.name, entry_price, exit_price, size, direction, reason)
                    equity += pnl
                    self.equity_curve.append({"Date": curr.name, "Equity": equity})
                    in_position = False

        return pd.DataFrame(self.trades), self.equity_curve

class BreakoutRetestStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Breakout Retest")

    def run(self, df, profile_data, capital=10000, risk_pct=0.01):
        """
        Logic: Trade confirmed breakouts of VA.
        1. Price breaks VAH.
        2. Price pulls back to retest VAH (within buffer).
        3. Price bounces off VAH to new high -> Enter LONG.
        Target: 2R.
        """
        self.trades = []
        equity = capital
        self.equity_curve = [{"Date": df.index[0], "Equity": equity}]
        
        vah = profile_data['vah']
        val = profile_data['val']
        buffer = vah * 0.002
        
        in_position = False
        direction = ""
        entry_price = 0
        stop_loss = 0
        size = 0
        entry_time = None
        
        # State machine for breakout
        pending_breakout = None # "VAH" or "VAL"
        
        for i in range(2, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            price = curr['Close']
            
            if not in_position:
                # Detect Breakout
                if price > vah and prev['Close'] < vah:
                    pending_breakout = "VAH"
                elif price < val and prev['Close'] > val:
                    pending_breakout = "VAL"
                
                # Check Retest Entry
                if pending_breakout == "VAH":
                    # Retest: Low touches VAH, Close is green/higher
                    if curr['Low'] <= (vah + buffer) and curr['Close'] > vah:
                        direction = "LONG"
                        entry_price = curr['Close']
                        stop_loss = vah - buffer # Stop inside VA
                        size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                        if size > 0:
                            in_position = True
                            entry_time = curr.name
                            pending_breakout = None
                
                elif pending_breakout == "VAL":
                    # Retest: High touches VAL, Close is red/lower
                    if curr['High'] >= (val - buffer) and curr['Close'] < val:
                        direction = "SHORT"
                        entry_price = curr['Close']
                        stop_loss = val + buffer # Stop inside VA
                        size = self.calculate_position_size(equity, risk_pct, entry_price, stop_loss)
                        if size > 0:
                            in_position = True
                            entry_time = curr.name
                            pending_breakout = None

            elif in_position:
                risk = abs(entry_price - stop_loss)
                target = entry_price + (risk * 2) if direction == "LONG" else entry_price - (risk * 2)
                
                hit_stop = (direction == "LONG" and price <= stop_loss) or \
                           (direction == "SHORT" and price >= stop_loss)
                hit_target = (direction == "LONG" and price >= target) or \
                             (direction == "SHORT" and price <= target)
                
                if hit_stop or hit_target:
                    exit_price = stop_loss if hit_stop else target
                    pnl = self.log_trade("BACKTEST", entry_time, curr.name, entry_price, exit_price, size, direction, "Target" if hit_target else "Stop")
                    equity += pnl
                    self.equity_curve.append({"Date": curr.name, "Equity": equity})
                    in_position = False

        return pd.DataFrame(self.trades), self.equity_curve
