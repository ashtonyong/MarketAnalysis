from volume_profile_engine import VolumeProfileEngine

def test_engine():
    print("Initializing Engine...")
    engine = VolumeProfileEngine()
    
    print("Fetching data for SPY...")
    df = engine.fetch_data("SPY", period="5d", interval="1h")
    
    if df.empty:
        print("Error: No data fetched.")
        return

    print(f"Data fetched: {len(df)} rows")
    print(df.head())

    print("Calculating Volume Profile...")
    profile = engine.calculate_volume_profile(df, num_bins=20)
    print("Profile head:")
    print(profile.head())
    
    total_volume = profile['Volume'].sum()
    print(f"Total Volume: {total_volume}")

    poc = engine.find_poc(profile)
    print(f"POC: {poc}")

    vah, val = engine.find_value_area(profile, total_volume, va_percent=0.70)
    print(f"VAH: {vah}")
    print(f"VAL: {val}")

if __name__ == "__main__":
    test_engine()
