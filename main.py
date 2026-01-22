import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate
import time

# 페이지 설정
st.set_page_config(page_title="은퇴 포트폴리오 트래커", layout="wide")

# 포트폴리오 매니저 초기화 (GitHub 연동 버전)
try:
    manager = PortfolioManager()
except Exception as e:
    st.error(f"GitHub 연결 오류: {e}")
    st.stop()

# --- 사이드바: 설정 및 기능 ---
st.sidebar.header("⚙️ 기능")

# 새로고침 버튼
if st.sidebar.button("🔄 가격 새로고침"):
    st.rerun()

st.sidebar.divider()

# 자산 추가 폼
st.sidebar.header("➕ 자산 추가하기")
with st.sidebar.form("add_asset_form"):
    st.caption("예: 삼성전자(005930.KS), NVDA, BTC-USD")
    ticker = st.text_input("종목 코드").upper().strip()
    asset_type = st.selectbox("자산 종류", ["Stock", "ETF", "Crypto", "Cash"])
    quantity = st.number_input("보유 수량", min_value=0.0, format="%.6f")
    avg_cost = st.number_input("평단가 (매수 통화 기준)", min_value=0.0, format="%.2f")
    
    submitted = st.form_submit_button("자산 추가")
    if submitted and ticker and quantity > 0:
        with st.spinner("GitHub에 저장 중..."):
            manager.add_asset(ticker, quantity, avg_cost, asset_type)
        st.sidebar.success(f"{ticker} 저장 완료!")
        time.sleep(1) # GitHub 반영 시간 벌기
        st.rerun()

# 자산 삭제 기능
st.sidebar.header("🗑️ 자산 삭제")
portfolio_list = manager.get_portfolio()
if portfolio_list:
    tickers = [item['ticker'] for item in portfolio_list]
    to_delete = st.sidebar.selectbox("삭제할 종목 선택", ["선택 안 함"] + tickers)
    if to_delete != "선택 안 함":
        if st.sidebar.button("삭제 확인"):
            with st.spinner("삭제 중..."):
                manager.remove_asset(to_delete)
            st.success(f"{to_delete} 삭제 완료!")
            time.sleep(1)
            st.rerun()

# --- 메인 화면 ---
