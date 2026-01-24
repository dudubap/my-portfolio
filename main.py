import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate
import time

st.set_page_config(page_title="은퇴 포트폴리오 30억 플랜", layout="wide")

try:
    manager = PortfolioManager()
except Exception as e:
    st.stop()

# --- 사이드바 ---
st.sidebar.header("⚙️ 자산 관리")
tab1, tab2 = st.sidebar.tabs(["➕ 신규 등록", "📝 수정/추매"])

# [Tab 1] 신규 등록
with tab1:
    with st.form("add_new"):
        st.caption("국내주식은 KRW, 미국주식은 USD를 선택하세요.")
        new_ticker = st.text_input("종목 코드 (예: 005930.KS, NVDA)").upper().strip()
        new_type = st.selectbox("자산 종류", ["Stock", "ETF", "Crypto", "Cash"])
        new_curr = st.radio("매수 통화", ["USD ($)", "KRW (₩)"], horizontal=True)
        
        new_qty = st.number_input("수량", min_value=0.0, format="%.6f")
        new_cost = st.number_input("평단가 (선택한 통화 기준)", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("등록하기"):
            if new_ticker and new_qty > 0:
                save_curr = "USD" if "USD" in new_curr else "KRW"
                with st.spinner("저장 중..."):
                    manager.add_asset(new_ticker, new_qty, new_cost, new_type, save_curr)
                time.sleep(1)
                st.rerun()

# [Tab 2] 수정/추매
with tab2:
    portfolio = manager.get_portfolio()
    if portfolio:
        tickers = [item['ticker'] for item in portfolio]
        selected_ticker = st.selectbox("종목 선택", tickers)
        cur_asset = next(i for i in portfolio if i['ticker'] == selected_ticker)
        
        asset_curr = cur_asset.get('currency', 'USD')
        symbol = "₩" if asset_curr == 'KRW' else "$"
        
        st.info(f"📊 보유: {cur_asset['quantity']:,.2f}주 / 평단: {symbol}{cur_asset['avg_cost']:,.2f}")
        
        edit_mode = st.radio("작업", ["추가 매수 (물타기)", "정보 수정"])
        
        with st.form("edit"):
            if edit_mode == "추가 매수 (물타기)":
                st.caption(f"👇 추가 매수한 가격을 **{asset_curr}** 기준으로 입력하세요.")
                add_q = st.number_input("추가 수량", min_value=0.0)
                add_p = st.number_input("매수 단가", min_value=0.0)
                
                org_q, org_c = cur_asset['quantity'], cur_asset['avg_cost']
                final_q = org_q + add_q
                final_c = ((org_q*org_c)+(add_q*add_p))/final_q if final_q>0 else org_c
                final_curr = asset_curr
            else:
                final_q = st.number_input("총 수량", value=float(cur_asset['quantity']))
                final_c = st.number_input("총 평단가", value=float(cur_asset['avg_cost']))
                curr_idx = 0 if asset_curr == 'USD' else 1
                new_curr_str = st.radio("통화 변경", ["USD", "KRW"], index=curr_idx, horizontal=True)
                final_curr = new_curr_str

            if st.form_submit_button("적용"):
                manager.
