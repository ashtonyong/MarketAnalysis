from volume_profile_engine import VolumeProfileEngine
from ai_agent_interface import VolumeProfileAgent
import json
import pandas as pd

def test_composite_logic():
    print("--- Testing Composite Logic ---")
    engine = VolumeProfileEngine()
    
    # Fetch 5 days of data
    print("Fetching 5d data for SPY...")
    df = engine.fetch_data("SPY", period="5d", interval="1h")
    
    if df.empty:
        print("Error: No data fetched.")
        return

    print(f"Data rows: {len(df)}")
    
    # Calculate composite
    print("Calculating composite profile...")
    profile = engine.calculate_composite_profile(df)
    
    print(f"Profile bins: {len(profile)}")
    print(f"Total Volume: {profile['Volume'].sum()}")
    
    poc = engine.find_poc(profile)
    print(f"Composite POC: {poc}")

def test_agent_composite():
    print("\n--- Testing Agent Composite API ---")
    agent = VolumeProfileAgent()
    
    # Test 5-day composite
    result = agent.analyze_composite("QQQ", days=5)
    print("5-Day Composite Result:")
    print(json.dumps(result, indent=2))
    
    # Test 10-day composite
    result_10 = agent.analyze_composite("IWM", days=10)
    print("\n10-Day Composite Result:")
    print(json.dumps(result_10, indent=2))

if __name__ == "__main__":
    test_composite_logic()
    test_agent_composite()
