from backtest_engine import RegimeBacktester
import pandas as pd

def test_backtest():
    print("Testing Regime Backtester...")
    ticker = "SPY"
    
    bt = RegimeBacktester(ticker)
    print(f"Running backtest for {ticker}...")
    
    res = bt.run_backtest()
    
    if res is not None and not res.empty:
        print("\nBacktest Results (Last 5 days):")
        print(res[['Close', 'Signal', 'Strategy_Equity', 'BuyHold_Equity']].tail())
        
        final_strat = res['Strategy_Equity'].iloc[-1]
        final_bh = res['BuyHold_Equity'].iloc[-1]
        
        print(f"\nFinal Strategy Equity: ${final_strat:,.2f}")
        print(f"Final Buy & Hold Equity: ${final_bh:,.2f}")
        
        if final_strat > final_bh:
            print("Strategy Outperformed!")
        else:
            print("Buy & Hold Outperformed.")
    else:
        print("Backtest failed.")

if __name__ == "__main__":
    test_backtest()
