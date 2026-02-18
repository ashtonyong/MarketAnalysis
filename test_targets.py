from price_targets import fetch_price_targets
import pandas as pd

def test_targets():
    ticker = "NVDA"
    print(f"Testing Price Targets for {ticker}...")
    data = fetch_price_targets(ticker)
    
    if "error" in data:
        print(f"Error: {data['error']}")
    else:
        print(f"Current Price: {data.get('current_price')}")
        print(f"Mean Target: {data.get('target_mean')}")
        print(f"High Target: {data.get('target_high')}")
        print(f"Low Target: {data.get('target_low')}")
        print(f"Analysts: {data.get('analyst_count')}")
        print(f"Recommendation: {data.get('recommendation')}")
        print(f"Rec Mean (1-5): {data.get('recommendation_mean')}")

if __name__ == "__main__":
    test_targets()
