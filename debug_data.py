import yfinance as yf
import pandas as pd

def test_ticker(symbol):
    print(f"\nTesting {symbol}...")
    t = yf.Ticker(symbol)
    
    # 1. Fast Info
    try:
        fi = t.fast_info
        print(f"FastInfo Last: {fi.last_price}")
        print(f"FastInfo Prev: {fi.previous_close}")
    except Exception as e:
        print(f"FastInfo Error: {e}")

    # 2. Regular Info
    try:
        info = t.info
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        print(f"Regular Info Price: {price}")
    except Exception as e:
        print(f"Regular Info Error: {e}")

    # 3. History
    try:
        hist = t.history(period="1d")
        if not hist.empty:
            print(f"History Last Close: {hist['Close'].iloc[-1]}")
        else:
            print("History: Empty")
    except Exception as e:
        print(f"History Error: {e}")

test_ticker("SPY")
test_ticker("BTC-USD")
