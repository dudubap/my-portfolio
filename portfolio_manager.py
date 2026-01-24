import streamlit as st
import json
from github import Github
from datetime import datetime

# Secrets에서 정보 가져오기
try:
    GITHUB_TOKEN = st.secrets["github"]["token"]
    REPO_NAME = st.secrets["github"]["repo_name"]
except:
    st.error("Secrets 설정이 안 되어 있습니다. 토큰과 저장소 이름을 확인하세요.")
    st.stop()

FILE_PATH = "portfolio.json"
HISTORY_PATH = "history.json"

class PortfolioManager:
    def __init__(self):
        # GitHub 로그인
        self.g = Github(GITHUB_TOKEN)
        self.repo = self.g.get_repo(REPO_NAME)
        self.portfolio = []
        self.history = []
        self._load_data()
        self._load_history()

    def _load_data(self):
        """포트폴리오(portfolio.json) 읽기"""
        try:
            contents = self.repo.get_contents(FILE_PATH)
            self.portfolio = json.loads(contents.decoded_content.decode("utf-8"))
        except:
            self.portfolio = []

    def _load_history(self):
        """기록(history.json) 읽기"""
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
        
        # 기록이 없거나 오늘 날짜가 아니면 추가
        if not self.history or self.history[-1]['date'] != today:
            self.history.append({"date": today, "value": total_value})
            self._save_history()
        
        # 오늘 날짜 기록이 이미 있으면 금액만 업데이트 (GitHub API 아끼기 위해 값이 다를 때만)
        elif self.history[-1]['date'] == today:
            if self.history[-1]['value'] != total_value:
                self.history[-1]['value'] = total_value
                self._save_history()

    def get_history(self):
        return self.history

    def add_asset(self, ticker, quantity, avg_cost, asset_type, dividend_yield=0.0):
        # 기존 자산 삭제 (
