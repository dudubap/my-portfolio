import streamlit as st
import json
from github import Github
import os
from datetime import datetime

# Secrets 정보
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo_name"]
FILE_PATH = "portfolio.json"
HISTORY_PATH = "history.json"  # 기록용 파일

class PortfolioManager:
    def __init__(self):
        self.g = Github(GITHUB_TOKEN)
        self.repo = self.g.get_repo(REPO_NAME)
        self.portfolio = []
        self.history = []
        self._load_data()
        self._load_history()

    def _load_data(self):
        """포트폴리오 불러오기"""
        try:
            contents = self.repo.get_contents(FILE_PATH)
            self.portfolio = json.loads(contents.decoded_content.decode("utf-8"))
        except:
            self.portfolio = []

    def _load_history(self):
        """과거 기록 불러오기"""
        try:
            contents = self.repo.get_contents(HISTORY_PATH)
            self.history = json.loads(contents.decoded_content.decode("utf-8"))
        except:
            self.history = []

    def _save_data(self):
        """포트폴리오 저장"""
        try:
            json_str = json.dumps(self.portfolio, indent=4, ensure_ascii=False)
            try:
                contents = self.repo.get_contents(FILE_PATH)
                self.repo.update_file(contents.path, "Update portfolio", json_str, contents.sha)
            except:
                self.repo.create_file(FILE_PATH, "Create portfolio", json_str)
        except Exception as e:
            st.error(f"저장 실패: {e}")

    def update_history(self, total_value):
        """오늘 날짜의 자산 총액을 기록 (하루에 한 번만 기록)"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 기록이 하나도 없거나, 마지막 기록 날짜가 오늘이 아니면 -> 새로 추가
        if not self.history or self.history[-1]['date'] != today:
            entry = {"date": today, "value": total_value}
            self.history.append(entry)
            self._save_history()
        
        # 2. 마지막 기록이 오늘 날짜면 -> 금액만 업데이트 (최신 상태 유지)
        elif self.history[-1]['date'] == today:
            # 금액이 다를 때만 업데이트 (GitHub API 호출 절약)
            if self.history[-1]['value'] != total_value:
                self.history[-1]['value'] = total_value
                self._save_history()

    def _save_history(self):
        """기록 파일(history.json) 저장"""
        try:
            json_str = json.dumps(self.history, indent=4, ensure_ascii=False)
            try:
                contents = self.repo.get_contents(HISTORY_PATH)
                self.repo.update_file(contents.path, "Update history", json_str, contents.sha)
            except:
                self.repo.create_file(HISTORY_PATH, "Create history", json_str)
        except Exception as e:
            print(f"히스토리 저장 실패: {e}")

    def get_history(self):
        return self.history

    # --- 기존 함수들 ---
    def add_asset(self, ticker, quantity, avg_cost, asset_type, dividend_yield=0.0):
        self.remove_asset(ticker, save=False) 
        asset = {
            "ticker": ticker,
            "quantity": float(quantity),
            "avg_cost": float(avg_cost),
            "type": asset_type,
            "dividend_yield": float(dividend_yield)
        }
        self.portfolio.append(asset)
        self._save_data()

    def remove_asset(self, ticker, save=True):
        self.portfolio = [item for item in self.portfolio if item['ticker'] != ticker]
        if save:
            self._save_data()

    def get_portfolio(self):
        return self.portfolio
