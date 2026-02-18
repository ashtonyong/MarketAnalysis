from econ_impact_overlay import EconomicCalendar, fetch_price_history
import pandas as pd
from datetime import datetime, timedelta

def test_econ():
    print("Testing Economic Calendar...")
    calendar = EconomicCalendar()
    
    # Test date range
    start_date = "2025-01-01"
    end_date = "2026-03-01"
    
    events = calendar.get_events(start_date, end_date)
    print(f"Events found between {start_date} and {end_date}: {len(events)}")
    for e in events:
        print(f" - {e['date']}: {e['event']} ({e['impact']})")
        
    print("\nTesting Price History Fetch...")
    df = fetch_price_history("SPY")
    if not df.empty:
        print(f"Price History: {len(df)} rows")
        print(f"Start: {df.index[0]}")
        print(f"End: {df.index[-1]}")
    else:
        print("Error: No price history fetched.")

if __name__ == "__main__":
    test_econ()
