"""
Risk Manager
Position sizing, risk:reward ratios, and portfolio heat calculations.
"""

from typing import Dict, List, Optional


class RiskManager:
    """
    Calculates position sizing and risk management metrics.
    """

    def __init__(self, account_size: float = 10000.0, risk_per_trade_pct: float = 1.0):
        self.account_size = account_size
        self.risk_per_trade_pct = risk_per_trade_pct

    @property
    def dollar_risk(self) -> float:
        """Maximum dollar risk per trade."""
        return self.account_size * (self.risk_per_trade_pct / 100)

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> Dict:
        """
        Calculate position size based on entry, stop, and risk tolerance.

        Args:
            entry_price: Planned entry price
            stop_loss: Stop loss price

        Returns:
            Dict with shares, dollar amounts, risk metrics
        """
        if entry_price <= 0 or stop_loss <= 0:
            return {'error': 'Prices must be positive'}

        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return {'error': 'Entry and stop loss cannot be the same'}

        max_shares = int(self.dollar_risk / risk_per_share)
        position_value = max_shares * entry_price
        actual_risk = max_shares * risk_per_share

        direction = 'LONG' if entry_price > stop_loss else 'SHORT'

        return {
            'direction': direction,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'shares': max_shares,
            'position_value': round(position_value, 2),
            'risk_per_share': round(risk_per_share, 2),
            'total_risk_dollars': round(actual_risk, 2),
            'total_risk_pct': round((actual_risk / self.account_size) * 100, 2),
            'account_utilization_pct': round((position_value / self.account_size) * 100, 2),
        }

    def multi_target_plan(self, entry_price: float, stop_loss: float,
                          targets: List[float]) -> Dict:
        """
        Create a trade plan with multiple profit targets and R:R ratios.

        Args:
            entry_price: Planned entry price
            stop_loss: Stop loss price
            targets: List of take profit prices

        Returns:
            Dict with R:R for each target and overall plan
        """
        pos = self.calculate_position_size(entry_price, stop_loss)
        if 'error' in pos:
            return pos

        risk_per_share = pos['risk_per_share']
        direction = pos['direction']
        target_details = []

        for i, tp in enumerate(targets, 1):
            if direction == 'LONG':
                reward = tp - entry_price
            else:
                reward = entry_price - tp

            r_multiple = reward / risk_per_share if risk_per_share > 0 else 0
            reward_dollars = pos['shares'] * reward
            required_win_rate = (1 / (1 + r_multiple)) * 100 if r_multiple > 0 else 100

            target_details.append({
                'target_num': i,
                'price': round(tp, 2),
                'reward_per_share': round(reward, 2),
                'reward_dollars': round(reward_dollars, 2),
                'r_multiple': round(r_multiple, 2),
                'rr_ratio': f"1:{r_multiple:.1f}",
                'required_win_rate': round(required_win_rate, 1),
                'quality': 'EXCELLENT' if r_multiple >= 3 else 'GOOD' if r_multiple >= 2 else 'FAIR' if r_multiple >= 1 else 'POOR',
            })

        return {
            'position': pos,
            'targets': target_details,
            'best_rr': max((t['r_multiple'] for t in target_details), default=0)
        }

    def portfolio_heat(self, open_positions: List[Dict]) -> Dict:
        """
        Calculate total portfolio risk from open positions.

        Args:
            open_positions: List of dicts with keys: ticker, shares, entry, stop_loss

        Returns:
            Dict with total heat, exposure, per-position breakdown
        """
        total_risk = 0
        total_exposure = 0
        breakdown = []

        for pos in open_positions:
            shares = pos.get('shares', 0)
            entry = pos.get('entry', 0)
            stop = pos.get('stop_loss', 0)

            risk_per_share = abs(entry - stop)
            position_risk = shares * risk_per_share
            position_value = shares * entry
            total_risk += position_risk
            total_exposure += position_value

            breakdown.append({
                'ticker': pos.get('ticker', '???'),
                'shares': shares,
                'entry': round(entry, 2),
                'stop_loss': round(stop, 2),
                'position_value': round(position_value, 2),
                'position_risk': round(position_risk, 2),
                'risk_pct': round((position_risk / self.account_size) * 100, 2),
            })

        heat_pct = (total_risk / self.account_size) * 100 if self.account_size > 0 else 0
        exposure_pct = (total_exposure / self.account_size) * 100 if self.account_size > 0 else 0

        # Risk assessment
        if heat_pct > 6:
            status = 'DANGER - Reduce positions'
        elif heat_pct > 4:
            status = 'WARNING - Elevated risk'
        elif heat_pct > 2:
            status = 'NORMAL - Acceptable'
        else:
            status = 'LOW - Room for more'

        return {
            'total_risk_dollars': round(total_risk, 2),
            'total_risk_pct': round(heat_pct, 2),
            'total_exposure': round(total_exposure, 2),
            'exposure_pct': round(exposure_pct, 2),
            'open_positions': len(open_positions),
            'status': status,
            'breakdown': breakdown,
        }


if __name__ == "__main__":
    rm = RiskManager(account_size=100000, risk_per_trade_pct=1.0)

    print("=" * 50)
    print("RISK MANAGER TEST")
    print("=" * 50)

    # Position sizing
    pos = rm.calculate_position_size(entry_price=175.00, stop_loss=172.50)
    print(f"\nPosition Size:")
    print(f"  Shares: {pos['shares']}")
    print(f"  Value: ${pos['position_value']:,.2f}")
    print(f"  Risk: ${pos['total_risk_dollars']:,.2f} ({pos['total_risk_pct']}%)")

    # Multi-target plan
    plan = rm.multi_target_plan(175.00, 172.50, [177.50, 180.00, 185.00])
    print(f"\nMulti-Target Plan:")
    for t in plan['targets']:
        print(f"  Target {t['target_num']}: ${t['price']} | R:R {t['rr_ratio']} | "
              f"Win Rate needed: {t['required_win_rate']}% | {t['quality']}")

    # Portfolio heat
    heat = rm.portfolio_heat([
        {'ticker': 'AAPL', 'shares': 100, 'entry': 175, 'stop_loss': 172},
        {'ticker': 'MSFT', 'shares': 50, 'entry': 370, 'stop_loss': 365},
    ])
    print(f"\nPortfolio Heat:")
    print(f"  Total Risk: ${heat['total_risk_dollars']:,.2f} ({heat['total_risk_pct']}%)")
    print(f"  Status: {heat['status']}")
