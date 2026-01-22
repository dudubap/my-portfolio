import streamlit as st
import json
from github import Github
import os

# Secrets에서 정보 가져오기
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo_name"]
FILE_PATH = "portfolio.json"

class PortfolioManager:
    def __init__(self):
        # GitHub 로그인
        self.g = Github(GITHUB_TOKEN)
        self.repo = self.g.get_repo(REPO_NAME)
        self.portfolio = []
        self._load_data()

    def _load_data(self):
        """GitHub에서 데이터 읽어오기"""
        try:
            contents = self.repo.get_contents(FILE_PATH)
            json_str = contents.decoded_content.decode("utf-8")
            self.portfolio = json.loads(json_str)
        except:
            self.portfolio = []

    def _save_data(self):
        """GitHub에 데이터 저장하기"""
        try:
            json_str = json.dumps(self.portfolio, indent=4, ensure_ascii=False)
            
            # 파일이 이미 있으면 업데이트
            try:
                contents = self.repo.get_contents(FILE_PATH)
                self.repo.update_file(contents.path, "Update portfolio data", json_str, contents.sha)
            except:
                # 파일이 없으면 새로 생성
                self.repo.create_file(FILE_PATH, "Create portfolio data", json_str)
                
        except Exception as e:
            st.error(f"저장 실패: {e}")

    def add_asset(self, ticker, quantity, avg_cost, asset_type):
        self.remove_asset(ticker, save=False) # 중복 제거
        asset = {
            "ticker": ticker,
            "quantity": float(quantity),
            "avg_cost": float(avg_cost),
            "type": asset_type
        }
        self.portfolio.append(asset)
        self._save_data() # 즉시 저장

    def remove_asset(self, ticker, save=True):
        self.portfolio = [item for item in self.portfolio if item['ticker'] != ticker]
        if save:
            self._save_data()

    def get_portfolio(self):
        return self.portfolio
