import streamlit as st
import json
from github import Github
from datetime import datetime

FILE_PATH = "portfolio.json"
HISTORY_PATH = "history.json"

class PortfolioManager:
    def __init__(self):
        # 1. 안전 장치: Secrets가 제대로 있는지 확인
        if "github" not in st.secrets:
            st.error("🚨 Secrets 설정이 없습니다. Streamlit 대시보드에서 Secrets를 확인해주세요.")
            st.stop()
            
        # 2. 정보 가져오기
        try:
            self.token = st.secrets["github"]["token"]
            self.repo_name = st.secrets["github"]["repo_name"]
        except KeyError:
            st.error("🚨 Secrets 형식이 잘못되었습니다. [github] 아래에 token과 repo_name이 있어야 합니다.")
            st.stop()

        # 3. GitHub 로그인 및 연결
        try:
            self.g = Github(self.token)
            self.repo = self.g.get_repo(self.repo_name)
        except Exception as e:
            st.error(f"🚨 GitHub 연결 실패: 저장소 이름({self.repo_name})이나 토큰을 확인하세요.\n에러: {e}")
            st.stop()
            
        self.portfolio = []
        self.history = []
        self._load_data()
        self._load_history()

    def _load_data(self):
        """포트폴리오 읽기"""
        try:
            contents = self.repo.get_contents(FILE_PATH)
            self.portfolio = json.loads(contents.decoded_content.decode("utf-8"))
        except:
            self.portfolio = []

    def _load_history(self):
        """기록 읽기"""
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

    def _save_history(self):
        """기록 저장"""
        try:
            json_str = json.dumps(self.history, indent=4, ensure_ascii=False)
            try:
                contents = self.repo.get_contents(HISTORY_PATH)
                self.repo.update_file(contents.path, "Update history", json_str, contents.sha)
            except:
                self.repo.create_file(HISTORY_PATH, "Create history", json_str)
        except Exception as e:
            print(f"히스토리 저장 실패: {e}")

    def update_history(self, total_value):
        """오늘 자산 기록 (하루 1번)"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not self.history or self.history[-1]['date'] != today:
            self.history.append({"date": today, "value": total_value})
            self._save_history()
        
        elif self.history[-1]['date'] == today:
            if self.history[-1]['value'] != total_value:
                self.history[-1]['value'] = total_value
                self._save_history()

    def get_history(self):
        return self.history

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
