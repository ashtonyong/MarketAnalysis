"""
Test Advanced Features
Verifies the return structure of all 5 new modules.
"""
from ai_agent_interface import VolumeProfileAgent
import pandas as pd

def test_all_advanced_features():
    ticker = "SPY"
    
    print(f"Testing Advanced Features for {ticker}...")
    print("="*60)
    
    # 1. Test Market Profile (TPO)
    print("\n[1] Testing Market Profile (TPO)...")
    mp = VolumeProfileAgent.get_market_profile_tpo(ticker)
    if mp['status'] == 'success':
        data = mp['data']
        print(f"   [OK] Success! Rows: {len(data['profile'])}")
        print(f"   [OK] Shape: {data['shape']['shape']}")
        print(f"   [OK] Day Type: {data['day_type']}")
        print(f"   [OK] IB: {data['initial_balance']['low']} - {data['initial_balance']['high']}")
    else:
        print(f"   [FAIL] Failed: {mp.get('error')}")
    
    # 2. Test Composite Profiles
    print("\n[2] Testing Composite Profiles...")
    composite = VolumeProfileAgent.get_composite_profile(ticker, num_days=5, weighting='exponential')
    if composite['status'] == 'success':
        data = composite['data']
        print(f"   [OK] Success! Days Included: {data['days']}")
        print(f"   [OK] Composite POC: ${data['poc']:.2f}")
    else:
        print(f"   [FAIL] Failed: {composite.get('error')}")
    
    # 3. Test Volume Nodes
    print("\n[3] Testing Volume Nodes...")
    nodes = VolumeProfileAgent.get_volume_nodes(ticker)
    if nodes['status'] == 'success':
        data = nodes['data']
        print(f"   [OK] HVN Clusters: {len(data['hvn_clusters'])}")
        print(f"   [OK] LVN Clusters: {len(data['lvn_clusters'])}")
        print(f"   [OK] Breakout Zones: {len(data['breakout_zones'])}")
        if data['breakout_zones']:
            print(f"     -> First Zone Width: {data['breakout_zones'][0]['width']:.3f} (S: {data['breakout_zones'][0]['strength']})")
    else:
        print(f"   [FAIL] Failed: {nodes.get('error')}")
    
    # 4. Test Pattern Detection
    print("\n[4] Testing Pattern Detection...")
    patterns = VolumeProfileAgent.get_pattern_detection(ticker)
    if patterns['status'] == 'success':
        data = patterns['data']
        ph = data['poor_highs_lows']['poor_high']
        print(f"   [OK] Poor High Detected? {ph['detected']}")
        print(f"   [OK] VA Status: {data['value_area_status']['status']}")
        print(f"   [OK] Excess Events: {len(data['excess'])}")
    else:
        print(f"   [FAIL] Failed: {patterns.get('error')}")
    
    # 5. Test Statistics
    print("\n[5] Testing Profile Statistics...")
    stats = VolumeProfileAgent.get_profile_statistics(ticker)
    if stats['status'] == 'success':
        data = stats['data']
        print(f"   [OK] Volatility: {data['profile_width']['volatility']}")
        print(f"   [OK] Bias: {data['volume_distribution']['bias']}")
        print(f"   [OK] Efficiency: {data['profile_efficiency']['efficiency_pct']:.2f}%")
        print(f"   [OK] Trend: {data['trend_indicators']['trend']}")
    else:
        print(f"   [FAIL] Failed: {stats.get('error')}")
    
    print("\n" + "="*60)
    print("Verification Complete.")

if __name__ == "__main__":
    test_all_advanced_features()
