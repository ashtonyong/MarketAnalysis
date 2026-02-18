from rs_rating import RSRating
import pandas as pd

def test_rs():
    print("Testing RS Rating...")
    tickers = ["NVDA", "AAPL", "PFE"] # Leader, Market Performer, Laggard (historically)
    
    for t in tickers:
        print(f"\n--- Analyzing {t} ---")
        rs = RSRating(t)
        rating, df, scores = rs.calculate_rating()
        
        if not df.empty:
            print(f"RS Rating: {rating}")
            print(f"Performance Metrics: {scores}")
            print(f"Data Points: {len(df)}")
        else:
            print("Failed to fetch data.")

if __name__ == "__main__":
    test_rs()
