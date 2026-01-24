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
                manager.add_asset(selected_ticker, final_q, final_c, cur_asset['type'], final_curr)
                st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 새로고침"): st.rerun()

# --- 메인 화면 ---
# [변경] 지저분한 입력창 제거하고 변수로 고정
target = 3000000000  # 30억 원
month_inv = 2000000   # 월 200만 원 (시뮬레이션용)
rate = 8.0            # 연 수익률 8% (시뮬레이션용)

st.title("🚀 나의 은퇴 현황판 (Goal: 30억)")

if portfolio:
    with st.spinner("자산 가치 계산 중..."):
        usd_rate = get_usd_krw_rate()
        st.caption(f"환율: 1 USD = {usd_rate:,.2f} KRW")
        
        data = []
        tot_val = 0
        tot_inv = 0
        
        for item in portfolio:
            p, market_curr, name = fetch_current_price(item['ticker'])
            if p is None: p, name, market_curr = 0, item['ticker'], "KRW"
            
            my_curr = item.get('currency', 'USD')
            
            # (A) 평가 금액 (현재가 기준)
            if market_curr == 'USD':
                val_krw = p * item['quantity'] * usd_rate
                current_price_krw = p * usd_rate
            else:
                val_krw = p * item['quantity']
                current_price_krw = p
            
            # (B) 매수 금액 (내 평단가 기준)
            if my_curr == 'USD':
                cost_krw = item['avg_cost'] * item['quantity'] * usd_rate
            else:
                cost_krw = item['avg_cost'] * item['quantity']
            
            data.append({
                "종목": name, 
                "티커": item['ticker'], 
                "종류": item['type'],
                "수량": item['quantity'], 
                "현재가(KRW)": current_price_krw, 
                "평가금액": val_krw, 
                "매수금액": cost_krw, 
                "수익": val_krw - cost_krw,
                "수익률": ((val_krw-cost_krw)/cost_krw*100) if cost_krw>0 else 0,
                "매수통화": my_curr
            })
            tot_val += val_krw
            tot_inv += cost_krw

        if tot_val > 0: manager.update_history(tot_val)

    # UI 표시
    if tot_val > 0:
        # [변경] 목표 달성률 게이지 바 (입력창 없이 깔끔하게 표시)
        prog = min(tot_val/target, 1.0)
        st.write(f"### 🚩 목표 달성률: **{prog*100:.2f}%** (목표: {target:,.0f} 원)")
        st.progress(prog)
        
        # 시뮬레이션 메시지 (변수로 계산)
        if month_inv > 0 and tot_val < target:
            r = rate / 100 / 12
            current = tot_val
            months = 0
            while current < target and months < 600:
                current = current * (1 + r) + month_inv
                months += 1
            years, remain = months // 12, months % 12
            st.info(f"💡 (참고) 현재 속도로 **월 {month_inv/10000:.0f}만원** 투자 시, **{years}년 {remain}개월 뒤** 목표 달성!")

    st.divider()
    
    # 핵심 지표
    c1, c2, c3 = st.columns(3)
    c1.metric("총 자산", f"{tot_val:,.0f} 원")
    c2.metric("총 투자원금", f"{tot_inv:,.0f} 원")
    c3.metric("총 수익", f"{tot_val-tot_inv:,.0f} 원", f"{(tot_val-tot_inv)/tot_inv*100:.2f}%")
    
    st.divider()
    
    # 차트
    c1, c2 = st.columns(2)
    hist = pd.DataFrame(manager.get_history())
    if not hist.empty:
        c1.plotly_chart(px.line(hist, x='date', y='value', title="자산 성장"), use_container_width=True)
    
    df = pd.DataFrame(data)
    if not df.empty:
        c2.plotly_chart(px.pie(df, values='평가금액', names='종목', title="자산 비중", hole=0.4), use_container_width=True)
    
    # 상세 표
    st.subheader("📋 상세 현황")
    df_show = df.copy()
    for c in ['현재가(KRW)', '평가금액', '매수금액', '수익']: 
        df_show[c] = df_show[c].apply(lambda x: f"{x:,.0f} 원")
    df_show['수익률'] = df_show['수익률'].apply(lambda x: f"{x:,.2f}%")
    
    st.dataframe(df_show[['종목', '티커', '매수통화', '수량', '현재가(KRW)', '매수금액', '평가금액', '수익률']], use_container_width=True, hide_index=True)
