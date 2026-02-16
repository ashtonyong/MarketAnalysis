"""
EXAMPLE: How Antigravity AI Agent Can Use Volume Profile Tool

This script shows various scenarios where an AI agent like Antigravity
would interact with the Volume Profile tool to help traders.
"""

from ai_agent_interface import VolumeProfileAgent
import json
import os


def scenario_1_simple_analysis():
    """
    Scenario: User says "Analyze SPY for me"
    Antigravity should: Run analysis and provide insights
    """
    print("\n" + "="*70)
    print("SCENARIO 1: Simple Analysis Request")
    print("="*70)
    print("User: 'Analyze SPY for me'\n")
    
    # Antigravity executes:
    result = VolumeProfileAgent.analyze("SPY", period="5d", interval="15m")
    
    if result['status'] == 'success':
        data = result['data']
        signals = data['trading_signals']
        
        # Antigravity responds to user:
        print(f"SPY Analysis:")
        print(f"Current Price: ${data['current_price']:.2f}")
        print(f"Position: {data['position']}")
        print(f"\nKey Levels:")
        print(f"  POC: ${data['poc']:.2f}")
        print(f"  VAH: ${data['vah']:.2f}")
        print(f"  VAL: ${data['val']:.2f}")
        print(f"\nTrading Signal: {signals['primary_signal']}")
        print(f"Action: {signals['action']}")
        print(f"Risk Level: {signals['risk_level']}")


def scenario_2_find_best_setup():
    """
    Scenario: User says "Which stocks have the best setup right now?"
    Antigravity should: Compare multiple stocks and rank them
    """
    print("\n" + "="*70)
    print("SCENARIO 2: Find Best Trading Setup")
    print("="*70)
    print("User: 'Which stocks have the best setup right now?'\n")
    
    # Antigravity executes:
    watchlist = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMD"]
    print(f"Scanning watchlist: {', '.join(watchlist)}...\n")
    
    comparison = VolumeProfileAgent.compare_tickers(watchlist, period="5d")
    
    if comparison['status'] == 'success':
        # Antigravity responds with top 3:
        print("Top 3 Trading Opportunities:\n")
        for i, stock in enumerate(comparison['comparison'][:3], 1):
            print(f"{i}. {stock['ticker']}")
            print(f"   Opportunity Score: {stock['opportunity_score']}/100")
            print(f"   Current: ${stock['current_price']:.2f}")
            print(f"   Position: {stock['position']}")
            print(f"   Distance from POC: {stock['distance_from_poc']:.2f}%\n")
        
        # Get detailed plan for #1
        if comparison['comparison']:
            best = comparison['best_opportunity']
            print(f"Detailed Plan for {best['ticker']}:")
            plan = VolumeProfileAgent.get_trading_plan(best['ticker'])
            if plan['status'] == 'success':
                p = plan['plan']
                print(f"   Bias: {p['bias']}")
                print(f"   Strategy: {p['strategy']}")
                if p['entry_zone']:
                    print(f"   Entry Zone: ${p['entry_zone']['min']:.2f} - ${p['entry_zone']['max']:.2f}")
                if p['stop_loss']:
                    print(f"   Stop Loss: ${p['stop_loss']:.2f}")


def scenario_3_trading_plan():
    """
    Scenario: User says "Give me a trading plan for AAPL"
    Antigravity should: Provide entry, exit, and stop loss levels
    """
    print("\n" + "="*70)
    print("SCENARIO 3: Generate Trading Plan")
    print("="*70)
    print("User: 'Give me a trading plan for AAPL'\n")
    
    # Antigravity executes:
    plan = VolumeProfileAgent.get_trading_plan("AAPL")
    
    if plan['status'] == 'success':
        p = plan['plan']
        
        print(f"Trading Plan for AAPL")
        print(f"Current Price: ${p['current_price']:.2f}\n")
        print(f"Market Bias: {p['bias']}")
        print(f"Strategy: {p['strategy']}\n")
        
        print("Key Levels:")
        print(f"  POC (Pivot): ${p['poc']:.2f}")
        print(f"  VAH (Resistance): ${p['vah']:.2f}")
        print(f"  VAL (Support): ${p['val']:.2f}\n")
        
        if p['entry_zone']:
            print(f"Entry Zone: ${p['entry_zone']['min']:.2f} - ${p['entry_zone']['max']:.2f}")
        if p['stop_loss']:
            print(f"Stop Loss: ${p['stop_loss']:.2f}")
        if p['target_1']:
            print(f"Target 1: ${p['target_1']:.2f}")
        if p['target_2']:
            print(f"Target 2: ${p['target_2']:.2f}")


def scenario_4_set_alerts():
    """
    Scenario: User says "Set up alerts for TSLA"
    Antigravity should: Generate alert recommendations
    """
    print("\n" + "="*70)
    print("SCENARIO 4: Set Up Price Alerts")
    print("="*70)
    print("User: 'Set up alerts for TSLA'\n")
    
    # Antigravity executes:
    alerts = VolumeProfileAgent.get_alerts("TSLA")
    
    if alerts['status'] == 'success':
        data = alerts['data']
        
        print(f"Alert Setup for TSLA")
        print(f"Current Price: ${data['current_price']:.2f}\n")
        print("Recommended Alerts:")
        
        for i, alert in enumerate(data['alerts'], 1):
            print(f"{i}. ${alert['level']:.2f} ({alert['type'].upper()})")
            print(f"   -> {alert['message']}")


def scenario_5_visual_report():
    """
    Scenario: User says "Show me a chart for NVDA"
    Antigravity should: Create visual dashboard
    """
    print("\n" + "="*70)
    print("SCENARIO 5: Create Visual Chart")
    print("="*70)
    print("User: 'Show me a chart for NVDA'\n")
    
    # Antigravity executes:
    # UPDATED PATH FOR WINDOWS LOCAL ENV
    output_path = "nvda_volume_profile.png"
    chart = VolumeProfileAgent.create_chart("NVDA", period="5d", interval="15m",
                                           output_path=output_path)
    
    if chart['status'] == 'success':
        print(f"Chart created successfully!")
        print(f"Saved to: {chart['chart_path']}")
        print(f"\n(Antigravity would now display this chart to the user)")


def scenario_6_morning_routine():
    """
    Scenario: User says "Run my morning analysis"
    Antigravity should: Automated multi-stock analysis
    """
    print("\n" + "="*70)
    print("SCENARIO 6: Automated Morning Routine")
    print("="*70)
    print("User: 'Run my morning analysis'\n")
    
    watchlist = ["SPY", "QQQ", "AAPL", "TSLA"]
    
    print(f"Running analysis on: {', '.join(watchlist)}\n")
    print("="*70)
    
    for ticker in watchlist:
        result = VolumeProfileAgent.analyze(ticker, period="5d")
        
        if result['status'] == 'success':
            data = result['data']
            signals = data['trading_signals']
            
            print(f"\n{ticker}:")
            print(f"  Price: ${data['current_price']:.2f} | {data['position'].split('(')[0].strip()}")
            print(f"  Signal: {signals['action']}")
            print(f"  POC: ${data['poc']:.2f} | VAH: ${data['vah']:.2f} | VAL: ${data['val']:.2f}")


def scenario_7_json_export():
    """
    Scenario: Antigravity needs structured data for further processing
    Shows how to get JSON output
    """
    print("\n" + "="*70)
    print("SCENARIO 7: JSON Export for AI Processing")
    print("="*70)
    print("Antigravity needs structured data...\n")
    
    # Get data in JSON format
    result = VolumeProfileAgent.analyze("AAPL", period="1mo")
    
    # Antigravity can now parse and process this data
    json_output = json.dumps(result, indent=2)
    
    print("JSON Output (first 500 chars):")
    print(json_output[:500] + "...")
    print("\n(Antigravity can now use this structured data for decision making)")


def main():
    """Run all scenarios"""
    print("\n" + "="*70)
    print("VOLUME PROFILE TOOL - ANTIGRAVITY AI AGENT INTEGRATION EXAMPLES")
    print("="*70)
    
    # Run all scenarios
    scenario_1_simple_analysis()
    scenario_2_find_best_setup()
    scenario_3_trading_plan()
    scenario_4_set_alerts()
    scenario_5_visual_report()
    scenario_6_morning_routine()
    scenario_7_json_export()
    
    print("\n" + "="*70)
    print("INTEGRATION COMPLETE")
    print("="*70)
    print("\nAntigravity AI Agent can now:")
    print("  * Analyze any stock on demand")
    print("  * Find best trading setups")
    print("  * Generate trading plans")
    print("  * Set up price alerts")
    print("  * Create visual charts")
    print("  * Run automated routines")
    print("  * Export structured data (JSON)")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
