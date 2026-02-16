
# test_new_features.py

def test_all_new_features():
    ticker = "SPY"
    
    print("\n--------------------------------------------------")
    print("Testing Priority Features (Phase 7 Refined)")
    print("--------------------------------------------------")
    
    from ai_agent_interface import VolumeProfileAgent

    # Test 1: Profile Comparison
    print("\n[1] Testing Profile Comparison...")
    comparison = VolumeProfileAgent.get_profile_comparison(ticker)
    if comparison['status'] == 'success':
        shift = comparison['data']['shift']
        print(f"   [OK] Direction: {shift['direction']}")
        print(f"   [OK] POC Shift: {shift['poc_shift_pct']:.2f}%")
        print(f"   [OK] Interpretation: {shift['interpretation']}")
    else:
        print(f"   [FAIL] {comparison.get('error')}")
    
    # Test 2: Migration Tracker
    print("\n[2] Testing Migration Tracker...")
    migration = VolumeProfileAgent.get_migration_tracker(ticker)
    if migration['status'] == 'success':
        data = migration['data']
        print(f"   [OK] Trend: {data['trend']}")
        print(f"   [OK] Velocity: {data['velocity']:.3f}%/day")
        print(f"   [OK] Context: {data['context']}")
        print(f"   [OK] Strength: {data['strength']:.1f}/100")
    else:
        print(f"   [FAIL] {migration.get('error')}")
    
    # Test 3: POC Zones
    print("\n[3] Testing POC Zones...")
    poc_zones = VolumeProfileAgent.get_poc_zones(ticker)
    if poc_zones['status'] == 'success':
        data = poc_zones['data']
        print(f"   [OK] Intraday POC: ${data['intraday']['poc']:.2f}")
        print(f"   [OK] Confluence Strength: {data['confluence_strength']}")
        if data['confluence']:
            print(f"   [OK] Confluence Zone 1: ${data['confluence'][0]['price']:.2f} ({data['confluence'][0]['timeframes']} TFs)")
    else:
        print(f"   [FAIL] {poc_zones.get('error')}")
    
    # Test 4: Time & Sales
    print("\n[4] Testing Time & Sales...")
    # First get current levels need to call engine directly or just pass dummy values for test if not strictly needed by find_large_prints (but scan_key_levels needs them)
    # Let's get them from comparison since we ran it
    if comparison['status'] == 'success':
        today = comparison['data']['today']
        tns = VolumeProfileAgent.get_time_and_sales(
            ticker, 
            today['poc'], 
            today['vah'], 
            today['val']
        )
        if tns['status'] == 'success':
            data = tns['data']
            print(f"   [OK] Large Prints Found: {len(data['large_prints'])}")
            if data['large_prints']:
                 print(f"      -> First Print: {data['large_prints'][0]['size']} @ ${data['large_prints'][0]['price']:.2f}")
                 print(f"         Interp: {data['large_prints'][0]['interpretation'].encode('ascii', 'ignore').decode('ascii')}")
                 
            poc_act = data['key_levels']['poc']
            print(f"   [OK] POC Activity Status: {poc_act['status']}")
            if poc_act['status'] == 'ACTIVE':
                print(f"      -> Bias: {poc_act['bias']}")
                print(f"      -> Volume: {poc_act['total_volume']}")
        else:
            print(f"   [FAIL] {tns.get('error')}")
    else:
        print("   [SKIP] Comparison failed, cannot get levels for T&S test")
    
    print("\n" + "="*50)
    print("Priority Features Verification Complete.")

if __name__ == "__main__":
    test_all_new_features()
