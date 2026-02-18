from range_dashboard import fetch_range_data
import pandas as pd

def test_range():
    ticker = "NVDA"
    print(f"Testing Range Data for {ticker}...")
    data = fetch_range_data(ticker)
    
    if "error" in data:
        print(f"Error: {data['error']}")
    else:
        print(f"Current Price: {data.get('current_price')}")
        print(f"52-Week High: {data.get('high_52')}")
        print(f"52-Week Low: {data.get('low_52')}")
        print(f"Position (0-1): {data.get('position')}")
        print(f"SMA 50: {data.get('sma_50')}")
        print(f"SMA 200: {data.get('sma_200')}")
        
        hist = data.get("history")
        print(f"History Length: {len(hist)}")
        print(f"Recent Close: {hist['Close'].iloc[-1]}")

if __name__ == "__main__":
    test_range()
