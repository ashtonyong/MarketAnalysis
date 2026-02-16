"""
AI Analysis Report Generator
Generates professional trading analysis from Volume Profile data.
100% FREE - No API keys, no LLM, pure rule-based logic.
"""

from typing import Dict, Optional
from datetime import datetime


class AIReportGenerator:
    """Generate professional volume profile analysis reports."""

    def __init__(self, metrics: Dict, ticker: str):
        self.m = metrics
        self.ticker = ticker

    def generate(self, patterns: Optional[Dict] = None,
                 session_data: Optional[Dict] = None) -> str:
        """Generate a full AI analysis report."""
        sections = [
            self._header(),
            self._market_structure(),
            self._volume_analysis(),
            self._key_levels(),
            self._position_analysis(),
            self._bias_and_outlook(),
        ]

        if patterns:
            sections.append(self._pattern_analysis(patterns))

        sections.append(self._action_plan())
        sections.append(self._risk_note())

        return "\n\n".join(sections)

    def _header(self) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return (
            f"**AI ANALYSIS REPORT -- {self.ticker}**\n"
            f"Generated: {now}"
        )

    def _market_structure(self) -> str:
        price = self.m.get('current_price', 0)
        poc = self.m.get('poc', 0)
        vah = self.m.get('vah', 0)
        val = self.m.get('val', 0)
        position = self.m.get('position', 'UNKNOWN')
        dist = self.m.get('distance_from_poc_pct', 0)

        # Determine structure
        if 'ABOVE' in position:
            structure = "BULLISH"
            detail = (
                f"Price is trading ABOVE the value area at ${price:.2f}, "
                f"which is {abs(dist):.1f}% above the Point of Control (${poc:.2f}). "
                "This indicates buyers are in control and the market has accepted "
                "higher prices. The auction is exploring upward."
            )
        elif 'BELOW' in position:
            structure = "BEARISH"
            detail = (
                f"Price is trading BELOW the value area at ${price:.2f}, "
                f"which is {abs(dist):.1f}% below the Point of Control (${poc:.2f}). "
                "This indicates sellers are in control and the market has rejected "
                "higher prices. The auction is exploring downward."
            )
        else:
            structure = "BALANCED / NEUTRAL"
            detail = (
                f"Price is trading INSIDE the value area at ${price:.2f}, "
                f"which is {abs(dist):.1f}% from the Point of Control (${poc:.2f}). "
                "The market is in a balanced state with two-sided trade. "
                "Neither buyers nor sellers have dominance."
            )

        return f"**1. MARKET STRUCTURE: {structure}**\n{detail}"

    def _volume_analysis(self) -> str:
        poc = self.m.get('poc', 0)
        vah = self.m.get('vah', 0)
        val = self.m.get('val', 0)
        va_width = vah - val if vah and val else 0
        price = self.m.get('current_price', 0)
        va_pct = (va_width / price * 100) if price else 0

        if va_pct < 1:
            vol_state = "TIGHT (Low Volatility)"
            vol_note = (
                "The value area is very narrow, indicating low volatility and "
                "high consensus on fair value. A breakout move is likely building. "
                "Watch for expansion."
            )
        elif va_pct < 3:
            vol_state = "NORMAL"
            vol_note = (
                "The value area width is normal, suggesting healthy two-sided "
                "participation. The market is trading in a balanced range with "
                "reasonable price discovery."
            )
        else:
            vol_state = "WIDE (High Volatility)"
            vol_note = (
                "The value area is wide, indicating high volatility and disagreement "
                "on fair value. This suggests a trending or news-driven market "
                "with large directional moves."
            )

        return (
            f"**2. VOLUME ANALYSIS: {vol_state}**\n"
            f"Value Area Range: ${val:.2f} - ${vah:.2f} (${va_width:.2f} width, {va_pct:.1f}%)\n"
            f"POC (Fair Value): ${poc:.2f}\n"
            f"{vol_note}"
        )

    def _key_levels(self) -> str:
        poc = self.m.get('poc', 0)
        vah = self.m.get('vah', 0)
        val = self.m.get('val', 0)

        return (
            f"**3. KEY LEVELS TO WATCH**\n"
            f"- VAH (Resistance): ${vah:.2f} -- Sellers likely to defend this level\n"
            f"- POC (Fair Value): ${poc:.2f} -- Highest volume node, strongest magnet\n"
            f"- VAL (Support): ${val:.2f} -- Buyers likely to defend this level\n"
            f"\nPOC acts as a magnet. Price tends to return to POC when extended. "
            f"VAH/VAL act as support and resistance boundaries."
        )

    def _position_analysis(self) -> str:
        price = self.m.get('current_price', 0)
        poc = self.m.get('poc', 0)
        vah = self.m.get('vah', 0)
        val = self.m.get('val', 0)
        position = self.m.get('position', 'UNKNOWN')

        if 'ABOVE' in position:
            analysis = (
                f"Price at ${price:.2f} is above VAH (${vah:.2f}). "
                "Two scenarios:\n"
                f"- CONTINUATION: If price holds above ${vah:.2f}, expect further upside. "
                "New buyers are accepting higher prices.\n"
                f"- REJECTION: If price fails to hold above ${vah:.2f}, expect a pullback "
                f"toward POC at ${poc:.2f}. This would be a failed auction."
            )
        elif 'BELOW' in position:
            analysis = (
                f"Price at ${price:.2f} is below VAL (${val:.2f}). "
                "Two scenarios:\n"
                f"- CONTINUATION: If price holds below ${val:.2f}, expect further downside. "
                "Sellers are in control.\n"
                f"- REJECTION: If price reclaims ${val:.2f}, expect a bounce "
                f"toward POC at ${poc:.2f}. This would be a failed breakdown."
            )
        else:
            dist_to_vah = vah - price if vah else 0
            dist_to_val = price - val if val else 0
            closer = "VAH (resistance)" if dist_to_vah < dist_to_val else "VAL (support)"
            analysis = (
                f"Price at ${price:.2f} is inside the value area. "
                f"Closer to {closer}.\n"
                "- RANGE TRADE: Fade moves to VAH and VAL boundaries.\n"
                f"- BREAKOUT WATCH: A break above ${vah:.2f} or below ${val:.2f} "
                "with volume signals a directional move."
            )

        return f"**4. POSITION ANALYSIS**\n{analysis}"

    def _bias_and_outlook(self) -> str:
        position = self.m.get('position', 'UNKNOWN')
        dist = self.m.get('distance_from_poc_pct', 0)

        if 'ABOVE' in position and dist > 2:
            bias = "BULLISH"
            outlook = (
                "The market structure is bullish with price accepted above value. "
                "Look for buying opportunities on pullbacks to VAH or POC. "
                "Avoid shorting into strength."
            )
        elif 'BELOW' in position and dist < -2:
            bias = "BEARISH"
            outlook = (
                "The market structure is bearish with price rejected from value. "
                "Look for selling opportunities on rallies to VAL or POC. "
                "Avoid buying into weakness."
            )
        elif abs(dist) < 1:
            bias = "NEUTRAL -- MEAN REVERSION"
            outlook = (
                "Price is near POC (fair value). The market is in balance. "
                "Expect rotational trade between VAH and VAL. "
                "Wait for a directional break before taking a trend position."
            )
        else:
            bias = "NEUTRAL -- WATCH FOR DIRECTION"
            outlook = (
                "The market is near the edge of value. "
                "A decisive break with volume will signal the next move. "
                "Be patient and let the market show its hand."
            )

        return f"**5. BIAS: {bias}**\n{outlook}"

    def _pattern_analysis(self, patterns: Dict) -> str:
        notes = []

        poor_hl = patterns.get('poor_highs_lows', {})
        if poor_hl.get('poor_high', {}).get('detected'):
            ph = poor_hl['poor_high']['price']
            notes.append(
                f"- POOR HIGH detected at ${ph:.2f}. This high is likely to be "
                "revisited and broken. Unfinished business above."
            )
        if poor_hl.get('poor_low', {}).get('detected'):
            pl = poor_hl['poor_low']['price']
            notes.append(
                f"- POOR LOW detected at ${pl:.2f}. This low is likely to be "
                "revisited and broken. Unfinished business below."
            )

        excess = patterns.get('excess', [])
        if excess:
            for e in excess[:2]:
                side = e.get('side', 'unknown')
                notes.append(
                    f"- EXCESS detected on the {side}. This indicates strong "
                    "rejection and a reliable boundary."
                )

        if not notes:
            notes.append("- No significant structural patterns detected.")

        return "**6. PATTERN SIGNALS**\n" + "\n".join(notes)

    def _action_plan(self) -> str:
        price = self.m.get('current_price', 0)
        poc = self.m.get('poc', 0)
        vah = self.m.get('vah', 0)
        val = self.m.get('val', 0)
        position = self.m.get('position', 'UNKNOWN')

        if 'ABOVE' in position:
            plan = (
                f"- PRIMARY: Buy pullbacks to ${vah:.2f} with stop below ${poc:.2f}\n"
                f"- SECONDARY: If price breaks below ${vah:.2f}, wait for retest\n"
                f"- AVOID: Shorting above value area"
            )
        elif 'BELOW' in position:
            plan = (
                f"- PRIMARY: Sell rallies to ${val:.2f} with stop above ${poc:.2f}\n"
                f"- SECONDARY: If price reclaims ${val:.2f}, exit shorts\n"
                f"- AVOID: Buying below value area"
            )
        else:
            plan = (
                f"- PRIMARY: Buy near ${val:.2f}, sell near ${vah:.2f} (range trade)\n"
                f"- BREAKOUT: Long above ${vah:.2f} or short below ${val:.2f}\n"
                f"- PIVOT: Watch POC at ${poc:.2f} for intraday direction"
            )

        return f"**ACTION PLAN**\n{plan}"

    def _risk_note(self) -> str:
        return (
            "---\n"
            "*This analysis is generated from Volume Profile data using rule-based "
            "logic. It is not financial advice. Always manage risk and use proper "
            "position sizing.*"
        )


# Quick test
if __name__ == "__main__":
    test_metrics = {
        'current_price': 681.50,
        'poc': 683.20,
        'vah': 690.00,
        'val': 678.50,
        'position': 'INSIDE VALUE AREA',
        'distance_from_poc_pct': -0.25,
    }

    report = AIReportGenerator(test_metrics, "SPY").generate()
    print(report)
