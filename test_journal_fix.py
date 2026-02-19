from trade_journal import TradeJournal
import pandas as pd

def test_journal():
    print("Testing TradeJournal...")
    j = TradeJournal()
    
    # Clear for test
    j.clear_all()
    
    # Add trades
    print("Adding trades...")
    j.add_trade('SPY', 'LONG', 500, 510, 10) # Win
    j.add_trade('QQQ', 'SHORT', 400, 405, 10) # Loss
    
    # Test get_stats
    print("Testing get_stats()...")
    stats = j.get_stats()
    print(f"Stats: {stats}")
    
    assert stats['total_trades'] == 2
    assert stats['wins'] == 1
    assert stats['losses'] == 1
    
    # Test get_recent_trades
    print("Testing get_recent_trades()...")
    recent = j.get_recent_trades()
    print("Recent Trades Head:")
    print(recent.head())
    
    assert not recent.empty
    assert 'ticker' in recent.columns
    
    print("✅ TradeJournal tests passed!")

if __name__ == "__main__":
    test_journal()
