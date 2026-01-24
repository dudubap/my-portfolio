import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate
import time

# 1. 페이지 설정
st.set_page_config(page_title="은퇴 포트폴리오 30억 플랜", layout="wide")

# 2. 매니저 연결
try:
    manager = PortfolioManager()
except Exception as e:
    st.error(f"GitHub 연결 실패: {e}")
    st.stop()

# --- 사이드바 ---
st.sidebar.header("⚙️ 포트폴리오 관리")

# 탭 나누기 (신규 vs 수정)
tab1, tab2 = st.sidebar.tabs(["➕ 신규 등록", "📝 수정/추매"])

# [Tab 1] 아예 새로운 종목 추가
with tab1:
    st.subheader("새로운 종목 추가")
    with st.form("add_new"):
        new_ticker = st.text_input("종목 코드 (예: TSLA)").upper().strip()
        new_type = st.selectbox("종류", ["Stock", "ETF", "Crypto", "Cash"])
        new_qty = st.number_input("수량", min_value=0.0, format="%.6f")
        new_cost = st.number_input("평단가", min_value=0.0, format="%.2f")
        new_div = st.number_input("예상 배당률 (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
        
        if st.form_submit_button("신규 등록"):
            if new_ticker and new_qty > 0:
                with st.spinner("등록 중..."):
                    manager.add_asset(new_ticker, new_qty, new_cost, new_type, new_div)
                time.sleep(1)
                st.rerun()

# [Tab 2] 기존 종목 수정 (계산기 기능)
with tab2:
    st.subheader("기존 자산 수정 / 추가 매수")
    portfolio = manager.get_portfolio()
    
    if not portfolio:
        st.info("먼저 '신규 등록' 탭에서 자산을 추가하세요.")
    else:
        # 1. 수정할 종목 선택
        tickers = [item['ticker'] for item in portfolio]
        selected_ticker = st.selectbox("종목 선택", tickers)
        
        # 선택한 종목의 현재 정보 가져오기
        current_asset = next(item for item in portfolio if item['ticker'] == selected_ticker)
        cur_qty = current_asset['quantity']
        cur_cost = current_asset['avg_cost']
        cur_div = current_asset.get('dividend_yield', 0.0)
        
        st.info(f"📊 **현재 상태**\n- 보유: {cur_qty:,.2f}주\n- 평단: {cur_cost:,.0f}원")
        
        # 수정 모드 선택
        edit_mode = st.radio("작업 선택", ["추가 매수 (물타기)", "직접 수정 (오타 정정)"])
        
        with st.form("update_existing"):
            if edit_mode == "추가 매수 (물타기)":
                st.caption("👇 이번에 산 것만 입력하세요. 알아서 합쳐줍니다.")
                added_qty = st.number_input("추가 매수 수량 (+)", min_value=0.0, format="%.6f")
                added_price = st.number_input("매수 단가 (가격)", min_value=0.0, format="%.2f")
                
                # 계산 로직
                new_total_qty = cur_qty + added_qty
                if new_total_qty > 0:
                    new_avg_cost = ((cur_qty * cur_cost) + (added_qty * added_price)) / new_total_qty
                else:
                    new_avg_cost = cur_cost
                
                # 미리보기
                if added_qty > 0:
                    st.markdown(f"""
                    **🔄 변경 예상 결과:**
                    - 수량: {cur_qty} ➝ **{new_total_qty:,.2f}**
                    - 평단: {cur_cost:,.0f} ➝ **{new_avg_cost:,.0f}**
                    """)
                    
            else: # 직접 수정
                st.caption("👇 데이터를 덮어씁니다.")
                new_total_qty = st.number_input("총 수량", value=float(cur_qty), format="%.6f")
                new_avg_cost = st.number_input("총 평단가", value=float(cur_cost), format="%.2f")
                new_div_
