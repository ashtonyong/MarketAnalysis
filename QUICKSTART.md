# 🚀 QUICK START GUIDE

## Step 1: Installation (2 minutes)

```bash
# Install dependencies
pip install pandas numpy yfinance matplotlib

# OR use the provided script
chmod +x setup.sh
./setup.sh
```

## Step 2: Run Your First Analysis (30 seconds)

```bash
# Quick analysis of SPY
python volume_profile_cli.py quick SPY

# Full analysis with chart
python volume_profile_cli.py analyze AAPL
```

## Step 3: Antigravity Integration (1 minute)

**In your Antigravity agent code:**

```python
from ai_agent_interface import VolumeProfileAgent

# When user asks to analyze a stock
result = VolumeProfileAgent.analyze("AAPL")
print(result)

# When user wants a trading plan
plan = VolumeProfileAgent.get_trading_plan("SPY")
print(plan)

# Compare multiple stocks
comparison = VolumeProfileAgent.compare_tickers(["AAPL", "MSFT", "GOOGL"])
print(comparison)
```

## What Antigravity Can Do With This Tool

### 1. **Answer "Analyze X stock"**
```python
VolumeProfileAgent.analyze("AAPL")
# Returns: Current price, POC, VAH, VAL, trading signals
```

### 2. **Answer "What's the best setup?"**
```python
VolumeProfileAgent.compare_tickers(["AAPL", "MSFT", "GOOGL", "TSLA"])
# Returns: Ranked list with opportunity scores
```

### 3. **Answer "Give me a trading plan for X"**
```python
VolumeProfileAgent.get_trading_plan("SPY")
# Returns: Entry zone, stop loss, targets, strategy
```

### 4. **Answer "Set alerts for X"**
```python
VolumeProfileAgent.get_alerts("TSLA")
# Returns: Alert levels for POC, VAH, VAL
```

### 5. **Answer "Show me a chart"**
```python
VolumeProfileAgent.create_chart("NVDA", output_path="chart.png")
# Returns: Path to saved chart image
```

## Example Antigravity Workflow

```python
# User: "Find me the best stock to trade today"

from ai_agent_interface import VolumeProfileAgent

# Step 1: Compare multiple stocks
watchlist = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
comparison = VolumeProfileAgent.compare_tickers(watchlist)

# Step 2: Get best opportunity
best = comparison['best_opportunity']

# Step 3: Get detailed plan
plan = VolumeProfileAgent.get_trading_plan(best['ticker'])

# Step 4: Create chart
chart = VolumeProfileAgent.create_chart(best['ticker'], output_path=f"{best['ticker']}_chart.png")

# Step 5: Return results to user
response = f"""
Best Trading Opportunity: {best['ticker']}
Opportunity Score: {best['opportunity_score']}/100
Current Price: ${best['current_price']:.2f}

Trading Plan:
- Bias: {plan['plan']['bias']}
- Strategy: {plan['plan']['strategy']}
- Entry Zone: ${plan['plan']['entry_zone']['min']:.2f} - ${plan['plan']['entry_zone']['max']:.2f}
- Stop Loss: ${plan['plan']['stop_loss']:.2f}

Chart saved to: {chart['chart_path']}
"""
```

## Quick Commands Reference

### CLI Commands
```bash
# Analyze with full report
python volume_profile_cli.py analyze TICKER [--period 1mo] [--interval 15m]

# Quick check
python volume_profile_cli.py quick TICKER

# Compare multiple
python volume_profile_cli.py compare TICKER1 TICKER2 TICKER3

# Export levels
python volume_profile_cli.py levels TICKER

# Visual chart
python volume_profile_visualizer.py TICKER
```

### Python API (for Antigravity)
```python
from ai_agent_interface import VolumeProfileAgent

# Full analysis
VolumeProfileAgent.analyze(ticker, period, interval)

# Trading plan
VolumeProfileAgent.get_trading_plan(ticker, period)

# Compare stocks
VolumeProfileAgent.compare_tickers(tickers, period)

# Get alerts
VolumeProfileAgent.get_alerts(ticker, period)

# Create chart
VolumeProfileAgent.create_chart(ticker, period, interval, output_path)
```

## Common Parameters

**ticker**: Stock symbol (e.g., "AAPL", "SPY", "TSLA")

**period**: Time range
- Intraday: "1d", "5d"
- Swing: "1mo", "3mo"
- Position: "6mo", "1y"

**interval**: Bar size
- Scalping: "1m", "5m"
- Day trading: "15m", "30m", "1h"
- Swing: "1d"

## Test It Works

Run the example file:
```bash
python example_antigravity_integration.py
```

This will show 7 different scenarios of how Antigravity can use the tool.

## Need Help?

1. Read the full **README.md** for detailed documentation
2. Check **example_antigravity_integration.py** for more examples
3. Each Python file has extensive docstrings
