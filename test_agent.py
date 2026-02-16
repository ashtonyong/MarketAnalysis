from ai_agent_interface import VolumeProfileAgent
import json

def test_agent():
    agent = VolumeProfileAgent()
    
    print("--- Testing analyze() for SPY ---")
    result = agent.analyze("SPY", period="5d")
    print(json.dumps(result, indent=2))
    
    if "error" not in result:
        print("\n--- Testing get_trading_plan() ---")
        plan = agent.get_trading_plan(result)
        print(json.dumps(plan, indent=2))

    print("\n--- Testing compare_tickers() ---")
    comparison = agent.compare_tickers(["SPY", "QQQ", "IWM"])
    print(json.dumps(comparison, indent=2))

if __name__ == "__main__":
    test_agent()
