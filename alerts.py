"""
Telegram Alert System for Volume Profile
Sends real-time notifications when price crosses key levels.
"""

import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
from volume_profile_engine import VolumeProfileEngine


class TelegramAlertBot:
    """Sends formatted alert messages via Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Telegram."""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"[Telegram Error] {e}")
            return False

    def send_alert(self, ticker: str, alert_type: str, level: float,
                   current_price: float, direction: str, action: str = "") -> bool:
        """Send a formatted price alert."""
        emoji = "🔴" if direction == "DOWN" else "🟢" if direction == "UP" else "🟡"
        msg = (
            f"{emoji} <b>ALERT: {ticker}</b>\n\n"
            f"<b>Type:</b> {alert_type}\n"
            f"<b>Level:</b> ${level:.2f}\n"
            f"<b>Current:</b> ${current_price:.2f}\n"
            f"<b>Direction:</b> {direction}\n"
        )
        if action:
            msg += f"\n<b>Action:</b> {action}"

        msg += f"\n\n<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        return self.send_message(msg)

    def send_scan_summary(self, results: List[Dict]) -> bool:
        """Send a summary of scanner results."""
        if not results:
            return self.send_message("📊 Scanner: No results.")

        lines = ["📊 <b>Scanner Results</b>\n"]
        for i, r in enumerate(results[:5], 1):
            lines.append(
                f"{i}. <b>{r['ticker']}</b> — Score: {r['opportunity_score']}/100 "
                f"| ${r['current_price']:.2f} | {r['position']}"
            )
        return self.send_message("\n".join(lines))


class AlertMonitor:
    """
    Monitors tickers for key level crosses and sends Telegram alerts.
    """

    def __init__(self, bot: TelegramAlertBot, watchlist: List[str],
                 period: str = "1mo", check_interval: int = 300):
        self.bot = bot
        self.watchlist = [t.upper() for t in watchlist]
        self.period = period
        self.check_interval = check_interval  # seconds
        # Track last known position to detect crosses
        self._last_position: Dict[str, str] = {}
        self._last_prices: Dict[str, float] = {}

    def check_once(self) -> List[Dict]:
        """Check all tickers once. Returns list of triggered alerts."""
        triggered = []

        for ticker in self.watchlist:
            try:
                engine = VolumeProfileEngine(ticker, self.period)
                metrics = engine.get_all_metrics()

                if not metrics or metrics.get('poc', 0) == 0:
                    continue

                current_price = metrics['current_price']
                position = metrics['position']
                poc = metrics['poc']
                vah = metrics['vah']
                val = metrics['val']

                prev_position = self._last_position.get(ticker)
                prev_price = self._last_prices.get(ticker, current_price)

                # Detect crosses
                alerts = []

                if prev_position and prev_position != position:
                    # Position changed — something crossed
                    if 'ABOVE' in position and 'ABOVE' not in (prev_position or ''):
                        alerts.append({
                            'type': 'Price crossed above VAH',
                            'level': vah,
                            'direction': 'UP',
                            'action': 'Breakout — watch for continuation'
                        })
                    elif 'BELOW' in position and 'BELOW' not in (prev_position or ''):
                        alerts.append({
                            'type': 'Price broke below VAL',
                            'level': val,
                            'direction': 'DOWN',
                            'action': 'Breakdown — watch for reversal or continuation'
                        })
                    elif 'INSIDE' in position:
                        if 'ABOVE' in (prev_position or ''):
                            alerts.append({
                                'type': 'Price re-entered Value Area from above',
                                'level': vah,
                                'direction': 'DOWN',
                                'action': 'Failed breakout — mean reversion possible'
                            })
                        elif 'BELOW' in (prev_position or ''):
                            alerts.append({
                                'type': 'Price re-entered Value Area from below',
                                'level': val,
                                'direction': 'UP',
                                'action': 'Reclaim — watch for move to POC'
                            })

                # POC proximity alert (within 0.3%)
                poc_dist = abs((current_price - poc) / poc) * 100
                if poc_dist < 0.3 and self._last_prices.get(ticker):
                    prev_dist = abs((prev_price - poc) / poc) * 100
                    if prev_dist >= 0.3:
                        direction = 'UP' if current_price > prev_price else 'DOWN'
                        alerts.append({
                            'type': 'Price approaching POC',
                            'level': poc,
                            'direction': direction,
                            'action': 'Watch for reaction at POC'
                        })

                # Send alerts
                for alert in alerts:
                    success = self.bot.send_alert(
                        ticker, alert['type'], alert['level'],
                        current_price, alert['direction'], alert['action']
                    )
                    alert['ticker'] = ticker
                    alert['current_price'] = current_price
                    alert['sent'] = success
                    triggered.append(alert)

                # Update tracking
                self._last_position[ticker] = position
                self._last_prices[ticker] = current_price

            except Exception as e:
                print(f"[Monitor Error] {ticker}: {e}")

        return triggered

    def monitor_loop(self):
        """Continuously monitor. Runs forever until interrupted."""
        print(f"🔔 Alert Monitor started — watching {len(self.watchlist)} tickers")
        print(f"   Check interval: {self.check_interval}s")
        print(f"   Press Ctrl+C to stop\n")

        # Initial scan to set baseline
        self.bot.send_message(
            f"🔔 <b>Alert Monitor Started</b>\n"
            f"Watching: {', '.join(self.watchlist)}\n"
            f"Interval: {self.check_interval}s"
        )
        self.check_once()

        while True:
            try:
                time.sleep(self.check_interval)
                triggered = self.check_once()
                if triggered:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Triggered {len(triggered)} alert(s)")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No alerts")
            except KeyboardInterrupt:
                print("\n🛑 Monitor stopped.")
                self.bot.send_message("🛑 <b>Alert Monitor Stopped</b>")
                break
            except Exception as e:
                print(f"[Loop Error] {e}")
                time.sleep(30)  # Wait before retry


if __name__ == "__main__":
    from alert_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WATCHLIST, CHECK_INTERVAL_SECONDS

    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Please configure alert_config.py with your Telegram bot token and chat ID!")
        print()
        print("Steps:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow prompts")
        print("3. Copy the bot token")
        print("4. Search for @userinfobot to get your chat ID")
        print("5. Paste both into alert_config.py")
    else:
        bot = TelegramAlertBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        # Send test message
        print("Sending test message...")
        if bot.send_message("✅ <b>Volume Profile Alerts Connected!</b>"):
            print("✅ Test message sent! Check your Telegram.")
        else:
            print("❌ Failed to send. Check your token and chat ID.")

        # Start monitoring
        monitor = AlertMonitor(bot, WATCHLIST, check_interval=CHECK_INTERVAL_SECONDS)
        monitor.monitor_loop()
