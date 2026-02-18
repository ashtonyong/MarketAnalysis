from institutional_tracker import InstitutionalTracker
import pandas as pd

def test_inst():
    print("Testing Institutional Tracker...")
    ticker = "AAPL"
    
    tracker = InstitutionalTracker(ticker)
    print(f"Fetching ownership for {ticker}...")
    
    data = tracker.fetch_data()
    
    if data:
        print("\nMajor Holders:")
        print(data.get('major'))
        
        print("\nTop Institutions (First 3):")
        inst = data.get('institutional')
        if inst is not None and not inst.empty:
            print(inst.head(3))
            
        print("\nTop Mutual Funds (First 3):")
        mf = data.get('mutual_fund')
        if mf is not None and not mf.empty:
            print(mf.head(3))
    else:
        print("No ownership data found.")

if __name__ == "__main__":
    test_inst()
