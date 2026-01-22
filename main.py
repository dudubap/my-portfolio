import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate
import time

# 1. 페이지 설정
st.set_page_config(page_title="은퇴 포트폴리오 트래커", layout="wide")

# 2. 매니저 연결
try:
    manager = PortfolioManager()
except Exception as e:
    st.error(f"GitHub 연결 실패: {e}")
    st.stop()

# --- 사이드바 ---
st.sidebar.header("⚙️ 메뉴")
if st.sidebar.button("🔄 가격 새로고침"):
    st.rerun()

st.sidebar.divider()

# 은퇴 목표 설정
st.sidebar.header("🎯 은퇴 목표")
target_asset = st.sidebar.number_input("목표 금액 (원)", value=2000000000, step=100000000, format="%d")
monthly_input = st.sidebar.number_input("월 추가 투자금 (원)", value=1500000, step=100000, format="%d")
exp_return_rate = st.sidebar.slider("목표 연 수익률 (%)", 0.0, 30.0, 8.0)

st.sidebar.divider()

# 자산 추가
st.sidebar.header("➕ 자산 추가")
with st.sidebar.form("add"):
    ticker = st.text_input("종목 코드 (예: 005930.KS, NVDA)").upper().strip()
    atype = st.selectbox("종류", ["Stock", "ETF", "Crypto", "Cash"])
    qty = st.number_input("수량", min_value=0.0, format="%.6f")
    cost = st.number_input("평단가", min_value=0.0, format="%.2f")
    if st.form_submit_button("저장"):
        if ticker:
            with st.spinner("저장 중..."):
                manager.add_asset(ticker, qty, cost, atype)
            time.sleep(1)
            st.rerun()

# 자산 삭제
portfolio = manager.get_portfolio()
if portfolio:
    st.sidebar.header("🗑️ 삭제")
    del_ticker = st.sidebar.selectbox("삭제할 종목", ["선택"] + [i['ticker'] for i in portfolio])
    if del_ticker != "선택" and st.sidebar.button("삭제 실행"):
        manager.remove_asset(del_ticker)
        st.rerun()

# --- 메인 화면 ---
st.title("🚀 나의 은퇴 현황판")

if not portfolio:
    st.info("사이드바에서 자산을 추가해주세요.")
else:
    # 데이터 계산
    with st.spinner("계산 중..."):
        usd = get_usd_krw_rate()
        st.caption(f"환율: 1 USD = {usd:,.2f} KRW")
        
        data = []
        total_val = 0
        total_inv = 0
        
        for item in portfolio:
            p, cur, name = fetch_current_price(item['ticker'])
            if p is None: p, name, cur = 0, item['ticker'], "KRW"
            
            # 화폐 단위 변환
            multiplier = usd if cur == 'USD' else 1
            
            val = p * item['quantity'] * multiplier
            cost = item['avg_cost'] * item['quantity'] * multiplier
            current_p_krw = p * multiplier
            
            data.append({
                "종목": name, 
                "티커": item['ticker'], 
                "종류": item['type'],
                "수량": item['quantity'],
                "현재가": current_p_krw,     # 숫자 (계산용)
                "잔고": val,               # 숫자 (차트용)
                "원금": cost,              # 숫자 (계산용)
                "수익": val - cost,        # 숫자 (계산용)
                "수익률": ((val-cost)/cost*100) if cost>0 else 0
            })
            total_val += val
            total_inv += cost

    if total_val > 0:
        # 1. 은퇴 목표 달성률
        progress = min(total_val / target_asset, 1.0)
        st.write(f"### 🚩 목표 달성률: **{progress*100:.2f}%** (목표: {target_asset:,.0f} 원)")
        st.progress(progress)
        
        # 2. 시뮬레이션 메시지
        if monthly_input > 0 and total_val < target_asset:
            r = exp_return_rate / 100 / 12
            current = total_val
            months = 0
            while current < target_asset and months < 600:
                current = current * (1 + r) + monthly_input
                months += 1
            
            years = months // 12
            remain_months = months % 12
            st.info(f"💡 매월 **{monthly_input:,.0f}원** 투자 시, **{years}년 {remain_months}개월 뒤** 은퇴 가능! (연 수익률 {exp_return_rate}% 가정)")

        st.divider()

        # 3. 핵심 지표 (큰 글씨)
        c1, c2, c3 = st.columns(3)
        c1.metric("총 자산", f"{total_val:,.0f} 원")
        c2.metric("투자 원금", f"{total_inv:,.0f} 원")
        c3.metric("총 수익", f"{total_val-total_inv:,.0f} 원", f"{(total_val-total_inv)/total_inv*100:.2f}%")
        
        # 4. 차트 (숫자 데이터 사용)
        c1, c2 = st.columns(2)
        df = pd.DataFrame(data)
        with c1:
            st.subheader("비중")
            st.plotly_chart(px.pie(df, values='잔고', names='종목', hole=0.4), use_container_width=True)
        with c2:
            st.subheader("자산군")
            st.plotly_chart(px.pie(df, values='잔고', names='종류', hole=0.4), use_container_width=True)

        # 5. 상세 표
        st.subheader("📋 상세 보유 현황")
        
        df_display = df.copy()
        
        # 콤마(,) 찍기 포맷팅
        df_display['현재가'] = df_display['현재가'].apply(lambda x: f"{x:,.0f} 원")
        df_display['잔고'] = df_display['잔고'].apply(lambda x: f"{x:,.0f} 원")
        df_display['원금'] = df_display['원금'].apply(lambda x: f"{x:,.0f} 원")
        df_display['수익'] = df_display['수익'].apply(lambda x: f"{x:,.0f} 원")
        df_display['수익률'] = df_display['수익률'].apply(lambda x: f"{x:,.2f}%")
        
        st.dataframe(
            df_display[['종목', '티커', '수량', '현재가', '잔고', '수익', '수익률']], 
            use_container_width=True,
            hide_index=True
        )
