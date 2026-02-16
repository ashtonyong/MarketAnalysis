# Volume Profile Advanced Analytics User Guide

This guide explains how to use the newly implemented advanced analytics features in the Volume Profile Dashboard.

## 1. Profile Comparison (Yesterday vs Today)

**Purpose**: Understand how value is shifting relative to the previous trading session.

**How to Use**:
- Go to **Tab 1: Market Analysis**.
- Look at the **"POC Profile Shift"** metric in the top row.
- **Interpretation**:
    - **Green (+%)**: Bullish migration. Value is moving higher. Buyers are in control.
    - **Red (-%)**: Bearish migration. Value is moving lower. Sellers are in control.
    - **Gray (~0%)**: Stable/Balanced. Market is consolidating.

**Visuals**:
- Dashed horizontal lines on the main chart represent Yesterday's POC (Y-POC), VAH (Y-VAH), and VAL (Y-VAL).
- Compare current price action relative to these levels to gauge acceptance or rejection.

## 2. Value Area Migration Tracker

**Purpose**: Identify the multi-day trend of value movement.

**How to Use**:
- Go to **Tab 1: Market Analysis**.
- Look at the **"Migration"** metric in the top row.
- **Metrics**:
    - **Trend**: UPTREND, DOWNTREND, or SIDEWAYS.
    - **Velocity**: Speed of migration (% change per day). High velocity indicates a strong trend.
    - **Strength**: Confidence score (0-100) based on trend persistence.

**Strategy**:
- **UPTREND**: Look for buying opportunities on pullbacks to Value Area Low (VAL).
- **DOWNTREND**: Look for shorting opportunities on rallies to Value Area High (VAH).

## 3. POC Zones (Multi-Timeframe Confluence)

**Purpose**: Pinpoint high-probability support and resistance zones where multiple timeframes agree.

**How to Use**:
- Go to **Tab 5: Advanced Analytics > Composite Profiles**.
- Click **"Build Composite"** (default 5-10 days).
- Check the **"Confluence Check"** section at the bottom.
- **Interpretation**:
    - **🎯 Confluence Zone**: A price level where Daily, Weekly, and/or Monthly POCs overlap.
    - These zones act as **major magnets** for price and strong support/resistance.

**Visuals**:
- On the main chart (Tab 1), the POC is now displayed as a **POC Zone** (shaded orange area) rather than a single thin line, reflecting the reality of price action.

## 4. Time & Sales (Order Flow)

**Purpose**: Detect aggressive institutional buying/selling and "smart money" activity.

**How to Use**:
- Go to **Tab 2: Order Flow (T&S)**.
- Click **"Analyze Order Flow"**.

### Features:
- **Activity at Key Levels**:
    - breakdowns of specific buying vs selling pressure at POC, VAH, and VAL.
    - **Bias**: GREEN (Bullish), RED (Bearish), or GRAY (Neutral).
    - Use this to confirm a breakout or reversal at a key level.

- **Large Prints (Aggressive Tape)**:
    - A rigorous scan of the tape for "Block Trades" (unusually large volume).
    - **🟢 Large Aggressive BUY**: Price moved UP on high volume (Accumulation).
    - **🔴 Large Aggressive SELL**: Price moved DOWN on high volume (Distribution).
    - **⚪ Neutral**: Likely a dark pool print or cross that didn't move price.

## Troubleshooting

- **Missing Data**: Ensure you have a stable internet connection as data is fetched live from Yahoo Finance.
- **"No aggressive large prints"**: This is normal during low-volume periods (e.g., lunch hour).
- **Chart Lag**: If the chart is slow, try reducing the "Period" to `5d` or `1mo`.
