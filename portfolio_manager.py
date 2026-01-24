import streamlit as st
import json
from github import Github
from datetime import datetime

FILE_PATH = "portfolio.json"
HISTORY_PATH = "history.json"

class PortfolioManager:
    def __init__(self):
        if "github" not in st.secrets:
            st.error("Secrets 설정 확인 필요")
            st.stop()
        try:
            self.g = Github(st.secrets["github"]["token"])
            self.repo = self.g.get_repo(st.secrets["github"]["repo_name"])
            self.portfolio = []
            self.history = []
            self._load_data()
            self._load_history()
        except Exception as e:
            st.error(f"GitHub 연결 실패: {e}")
            st.stop()

    def _load_data(self):
        try:
            c = self.repo.get_contents(FILE_PATH)
            self.portfolio = json.loads(c.decoded_content.decode("utf-8"))
        except: self.portfolio = []

    def _load_history(self):
        try:
            c = self.repo.get_contents(HISTORY_PATH)
            self.history = json.loads(c.decoded_content.decode("utf-8"))
        except: self.history = []

    def _save_data(self):
        try:
            json_str = json.dumps(self.portfolio, indent=4, ensure_ascii=False)
            try:
                c = self.repo.get_contents(FILE_PATH)
                self.repo.update_file(c.path, "Update", json_str, c.sha)
            except:
                self.repo.create_file(FILE_PATH, "Create", json_str)
        except: pass

    def _save_history(self):
        try:
            json_str = json.dumps(self.history, indent=4, ensure_ascii=False)
            try:
                c = self.repo.get_contents(HISTORY_PATH)
                self.repo.update_file(c.path, "Update Hist", json_str, c.sha)
            except:
                self.repo.create_file(HISTORY_PATH, "Create Hist", json_str)
        except: pass

    def update_history(self, val):
        today = datetime.now().strftime("%Y-%m-%d")
        if not self.history or self.history[-1]['date'] != today:
            self.history.append({"date": today, "value": val})
            self._save_history()
        elif self.history[-1]['date'] == today and self.history[-1]['value'] != val:
            self.history[-1]['value'] = val
            self._save_history()
    
    def get_history(self): return self.history

    # [중요] dividend_yield 파라미터 부활!
    def add_asset(self, ticker, quantity, avg_cost, asset_type, dividend_yield=0.0):
        self.remove_asset(ticker, save=False)
        asset = {
            "ticker": ticker,
            "quantity": float(quantity),
            "avg_cost": float(avg_cost),
            "type": asset_type,
            "dividend_yield": float(dividend_yield) # 사용자가 입력한 값 저장
        }
        self.portfolio.append(asset)
        self._save_data()

    def remove_asset(self, ticker, save=True):
        self.portfolio = [item for item in self.portfolio if item['ticker'] != ticker]
        if save: self._save_data()

    def get_portfolio(self): return self.portfolio
