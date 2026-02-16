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
        self.price = metrics.get('current_price', 0)
        self.poc = metrics.get('poc', 0)
        self.vah = metrics.get('vah', 0)
        self.val = metrics.get('val', 0)
        self.position = metrics.get('position', 'UNKNOWN')
        self.dist = metrics.get('distance_from_poc_pct', 0)
        self.va_width = self.vah - self.val if self.vah and self.val else 0
        self.va_pct = (self.va_width / self.price * 100) if self.price else 0
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate(self, patterns: Optional[Dict] = None,
                 session_data: Optional[Dict] = None) -> str:
        """Generate a full AI analysis report."""
        sections = [
            self._header(),
            self._executive_summary(),
            self._level_table(),
            self._market_structure(),
            self._volume_analysis(),
            self._position_analysis(),
            self._action_plan(),
        ]

        if patterns:
            sections.append(self._pattern_analysis(patterns))

        sections.append(self._disclaimer())

        return "\n\n".join(sections)

    def generate_downloadable(self, patterns: Optional[Dict] = None) -> str:
        """Generate a plain-text version for download (no markdown)."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  VOLUME PROFILE ANALYSIS REPORT")
        lines.append(f"  {self.ticker}")
        lines.append(f"  Generated: {self.timestamp}")
        lines.append("=" * 60)
        lines.append("")

        # Executive Summary
        bias = self._get_bias()
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 40)
        lines.append(f"  Ticker:    {self.ticker}")
        lines.append(f"  Price:     ${self.price:.2f}")
        lines.append(f"  Bias:      {bias}")
        lines.append(f"  Position:  {self.position}")
        lines.append(f"  Distance:  {self.dist:.2f}% from POC")
        lines.append("")

        # Key Levels
        lines.append("KEY LEVELS")
        lines.append("-" * 40)
        lines.append(f"  VAH (Resistance):  ${self.vah:.2f}")
        lines.append(f"  POC (Fair Value):  ${self.poc:.2f}")
        lines.append(f"  VAL (Support):     ${self.val:.2f}")
        lines.append(f"  VA Width:          ${self.va_width:.2f} ({self.va_pct:.1f}%)")
        lines.append("")

        # Market Structure
        lines.append("MARKET STRUCTURE")
        lines.append("-" * 40)
        structure, detail = self._get_structure_detail()
        lines.append(f"  Structure: {structure}")
        lines.append(f"  {detail}")
        lines.append("")

        # Volume Profile
        lines.append("VOLUME PROFILE")
        lines.append("-" * 40)
        vol_state, vol_note = self._get_volume_state()
        lines.append(f"  State: {vol_state}")
        lines.append(f"  {vol_note}")
        lines.append("")

        # Position Scenarios
        lines.append("POSITION ANALYSIS")
        lines.append("-" * 40)
        for line in self._get_position_scenarios():
            lines.append(f"  {line}")
        lines.append("")

        # Action Plan
        lines.append("ACTION PLAN")
        lines.append("-" * 40)
        for line in self._get_action_lines():
            lines.append(f"  {line}")
        lines.append("")

        # Patterns
        if patterns:
            lines.append("PATTERN SIGNALS")
            lines.append("-" * 40)
            for line in self._get_pattern_lines(patterns):
                lines.append(f"  {line}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("  This report is generated from Volume Profile data")
        lines.append("  using rule-based analysis. Not financial advice.")
        lines.append("=" * 60)

        return "\n".join(lines)

    # --- Internal helpers ---

    def _get_bias(self) -> str:
        if 'ABOVE' in self.position and self.dist > 2:
            return "BULLISH"
        elif 'BELOW' in self.position and self.dist < -2:
            return "BEARISH"
        elif abs(self.dist) < 1:
            return "NEUTRAL (Mean Reversion Zone)"
        else:
            return "NEUTRAL (Watch for Direction)"

    def _get_structure_detail(self):
        if 'ABOVE' in self.position:
            return "BULLISH", (
                "Price is above the value area. Buyers are in control "
                "and the market has accepted higher prices."
            )
        elif 'BELOW' in self.position:
            return "BEARISH", (
                "Price is below the value area. Sellers are in control "
                "and the market has rejected higher prices."
            )
        else:
            return "BALANCED", (
                "Price is inside the value area. The market is in a balanced "
                "state with two-sided trade."
            )

    def _get_volume_state(self):
        if self.va_pct < 1:
            return "TIGHT (Low Volatility)", (
                "Value area is very narrow -- low volatility, high consensus. "
                "A breakout move is likely building."
            )
        elif self.va_pct < 3:
            return "NORMAL", (
                "Value area width is normal -- healthy two-sided participation "
                "with reasonable price discovery."
            )
        else:
            return "WIDE (High Volatility)", (
                "Value area is wide -- high volatility, disagreement on fair value. "
                "Trending or news-driven market."
            )

    def _get_position_scenarios(self):
        if 'ABOVE' in self.position:
            return [
                f"Price at ${self.price:.2f} is above VAH (${self.vah:.2f}).",
                f"IF HOLDS ABOVE ${self.vah:.2f}: Expect continuation higher.",
                f"IF REJECTED: Pullback toward POC at ${self.poc:.2f}.",
            ]
        elif 'BELOW' in self.position:
            return [
                f"Price at ${self.price:.2f} is below VAL (${self.val:.2f}).",
                f"IF HOLDS BELOW ${self.val:.2f}: Expect continuation lower.",
                f"IF RECLAIMS: Bounce toward POC at ${self.poc:.2f}.",
            ]
        else:
            dist_to_vah = self.vah - self.price if self.vah else 0
            dist_to_val = self.price - self.val if self.val else 0
            closer = "VAH (resistance)" if dist_to_vah < dist_to_val else "VAL (support)"
            return [
                f"Price at ${self.price:.2f} is inside value area, closer to {closer}.",
                f"RANGE: Fade moves to VAH/VAL boundaries.",
                f"BREAKOUT: Watch ${self.vah:.2f} above or ${self.val:.2f} below.",
            ]

    def _get_action_lines(self):
        if 'ABOVE' in self.position:
            return [
                f"PRIMARY: Buy pullbacks to ${self.vah:.2f}, stop below ${self.poc:.2f}",
                f"SECONDARY: If breaks below ${self.vah:.2f}, wait for retest",
                "AVOID: Shorting into strength above value area",
            ]
        elif 'BELOW' in self.position:
            return [
                f"PRIMARY: Sell rallies to ${self.val:.2f}, stop above ${self.poc:.2f}",
                f"SECONDARY: If reclaims ${self.val:.2f}, exit shorts",
                "AVOID: Buying into weakness below value area",
            ]
        else:
            return [
                f"PRIMARY: Buy near ${self.val:.2f}, sell near ${self.vah:.2f} (range)",
                f"BREAKOUT: Long above ${self.vah:.2f} or short below ${self.val:.2f}",
                f"PIVOT: Watch POC at ${self.poc:.2f} for intraday direction",
            ]

    def _get_pattern_lines(self, patterns):
        notes = []
        poor_hl = patterns.get('poor_highs_lows', {})
        if poor_hl.get('poor_high', {}).get('detected'):
            ph = poor_hl['poor_high']['price']
            notes.append(f"POOR HIGH at ${ph:.2f} -- likely to be revisited and broken")
        if poor_hl.get('poor_low', {}).get('detected'):
            pl = poor_hl['poor_low']['price']
            notes.append(f"POOR LOW at ${pl:.2f} -- likely to be revisited and broken")
        excess = patterns.get('excess', [])
        for e in excess[:2]:
            notes.append(f"EXCESS on {e.get('side', 'unknown')} -- strong rejection boundary")
        if not notes:
            notes.append("No significant structural patterns detected.")
        return notes

    # --- Markdown report sections ---

    def _header(self) -> str:
        return (
            f"### Volume Profile Analysis: {self.ticker}\n"
            f"*Report generated: {self.timestamp}*"
        )

    def _executive_summary(self) -> str:
        bias = self._get_bias()

        return (
            "#### Executive Summary\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| **Ticker** | {self.ticker} |\n"
            f"| **Current Price** | ${self.price:.2f} |\n"
            f"| **Bias** | **{bias}** |\n"
            f"| **Position** | {self.position} |\n"
            f"| **Distance from POC** | {self.dist:.2f}% |"
        )

    def _level_table(self) -> str:
        return (
            "#### Key Levels\n\n"
            "| Level | Price | Description |\n"
            "|-------|-------|-------------|\n"
            f"| **VAH** (Resistance) | ${self.vah:.2f} | Sellers likely to defend |\n"
            f"| **POC** (Fair Value) | ${self.poc:.2f} | Highest volume node, price magnet |\n"
            f"| **VAL** (Support) | ${self.val:.2f} | Buyers likely to defend |\n"
            f"| **VA Width** | ${self.va_width:.2f} ({self.va_pct:.1f}%) | "
            f"{'Tight' if self.va_pct < 1 else 'Normal' if self.va_pct < 3 else 'Wide'} |"
        )

    def _market_structure(self) -> str:
        structure, detail = self._get_structure_detail()
        return (
            f"#### Market Structure: {structure}\n\n"
            f"Price is trading at **${self.price:.2f}**, which is "
            f"**{abs(self.dist):.1f}%** {'above' if self.dist > 0 else 'below'} "
            f"the Point of Control (${self.poc:.2f}).\n\n"
            f"{detail}"
        )

    def _volume_analysis(self) -> str:
        vol_state, vol_note = self._get_volume_state()
        return (
            f"#### Volume Profile: {vol_state}\n\n"
            f"Value Area Range: **${self.val:.2f}** to **${self.vah:.2f}** "
            f"(${self.va_width:.2f} width, {self.va_pct:.1f}% of price)\n\n"
            f"{vol_note}"
        )

    def _position_analysis(self) -> str:
        scenarios = self._get_position_scenarios()
        body = "\n".join(f"- {s}" for s in scenarios)
        return f"#### Position Analysis\n\n{body}"

    def _action_plan(self) -> str:
        actions = self._get_action_lines()
        body = "\n".join(f"- **{a.split(':')[0]}**: {':'.join(a.split(':')[1:]).strip()}" for a in actions)
        return f"#### Action Plan\n\n{body}"

    def _pattern_analysis(self, patterns: Dict) -> str:
        notes = self._get_pattern_lines(patterns)
        body = "\n".join(f"- {n}" for n in notes)
        return f"#### Pattern Signals\n\n{body}"

    def _disclaimer(self) -> str:
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

    gen = AIReportGenerator(test_metrics, "SPY")
    print("=== MARKDOWN REPORT ===")
    print(gen.generate())
    print("\n\n=== DOWNLOAD REPORT ===")
    print(gen.generate_downloadable())
