from analyst_ratings import AnalystRatings
import pandas as pd

def test_analyst():
    print("Testing Analyst Ratings...")
    ticker = "AAPL"
    
    ar = AnalystRatings(ticker)
    print(f"Fetching ratings for {ticker}...")
    
    df = ar.fetch_upgrades_downgrades()
    
    if not df.empty:
        print("\nRecent Analyst Actions (Last 5):")
        print(df[['Firm', 'ToGrade', 'FromGrade', 'Action']].head())
        
        stats = ar.get_summary_stats(df)
        print("\nSummary Stats:")
        print(stats)
    else:
        print("No ratings found.")

if __name__ == "__main__":
    test_analyst()
