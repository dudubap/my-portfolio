import json
import os

DATA_FILE = "portfolio.json"

class PortfolioManager:
    def __init__(self):
        self.portfolio = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.portfolio = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.portfolio = []
        else:
            self.portfolio = []

    def _save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.portfolio, f, indent=4, ensure_ascii=False)

    def add_asset(self, ticker, quantity, avg_cost, asset_type):
        self.remove_asset(ticker)
        asset = {
            "ticker": ticker,
            "quantity": float(quantity),
            "avg_cost": float(avg_cost),
            "type": asset_type
        }
        self.portfolio.append(asset)
        self._save_data()

    def remove_asset(self, ticker):
        self.portfolio = [item for item in self.portfolio if item['ticker'] != ticker]
        self._save_data()

    def get_portfolio(self):
        return self.portfolio