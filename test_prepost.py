from prepost_tracker import PrePostTracker
import pandas as pd

def test_prepost():
    print("Testing Pre/Post Tracker...")
    tickers = ["SPY", "NVDA"]
    
    tracker = PrePostTracker(tickers)
    print(f"Tracking: {tickers}")
    
    df = tracker.fetch_data()
    
    if not df.empty:
        print("\nTracker Results:")
        print(df)
    else:
        print("No data returned. Market might be closed or data unavailable.")

if __name__ == "__main__":
    test_prepost()
