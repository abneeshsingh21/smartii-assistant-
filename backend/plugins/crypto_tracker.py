"""
Crypto Tracker Plugin
Track cryptocurrency prices and portfolio
"""

import sys
sys.path.append('..')
from plugin_system import Plugin as BasePlugin
import logging

logger = logging.getLogger(__name__)

class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Crypto Tracker"
        self.version = "1.0.0"
        self.description = "Track cryptocurrency prices, alerts, and portfolio"
        self.enabled = True
        
        self.register_command("price", self.get_price)
        self.register_command("portfolio", self.get_portfolio)
        self.register_command("alert", self.set_price_alert)
        self.register_command("trending", self.get_trending)
        
    async def initialize(self):
        logger.info("Crypto Tracker plugin initialized")
        
    async def get_price(self, params):
        """Get cryptocurrency price"""
        symbol = params.get("symbol", "BTC").upper()
        
        # Mock prices (replace with real API like CoinGecko)
        prices = {
            "BTC": {"price": 45000, "change_24h": 2.5},
            "ETH": {"price": 3200, "change_24h": -1.2},
            "SOL": {"price": 120, "change_24h": 5.8},
            "DOGE": {"price": 0.15, "change_24h": 3.2}
        }
        
        if symbol in prices:
            data = prices[symbol]
            return {
                "success": True,
                "symbol": symbol,
                "price": data["price"],
                "change_24h": data["change_24h"],
                "message": f"{symbol} is at ${data['price']:,.2f} ({data['change_24h']:+.2f}%)"
            }
        
        return {"error": f"Price for {symbol} not found"}
        
    async def get_portfolio(self, params):
        """Get portfolio value"""
        return {
            "success": True,
            "total_value": 125000.50,
            "holdings": [
                {"symbol": "BTC", "amount": 2.5, "value": 112500},
                {"symbol": "ETH", "amount": 3.5, "value": 11200},
                {"symbol": "SOL", "amount": 10, "value": 1200}
            ],
            "24h_change": 2.3
        }
        
    async def set_price_alert(self, params):
        """Set price alert"""
        symbol = params.get("symbol", "")
        target_price = params.get("price", 0)
        
        return {
            "success": True,
            "message": f"Alert set for {symbol} at ${target_price}",
            "symbol": symbol,
            "target_price": target_price
        }
        
    async def get_trending(self, params):
        """Get trending cryptocurrencies"""
        return {
            "success": True,
            "trending": [
                {"symbol": "SOL", "reason": "Up 15% today"},
                {"symbol": "MATIC", "reason": "New partnership"},
                {"symbol": "AVAX", "reason": "High volume"}
            ]
        }