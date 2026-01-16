import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate

# 페이지 설정
st.set_page_config(page_title="은퇴 포트폴리오 트래커", layout="wide")

# 포트폴리오 매니저 초기화
manager = PortfolioManager()

# --- 사이드바: 자산 추가 ---
st.sidebar.header("➕ 자산 추가하기")
with st.sidebar.form("add_asset_form"):
    st.caption("예: 삼성전자(005930.KS), 애플(AAPL), 비트코인(BTC-USD)")
    ticker = st.text_input("종목 코드").upper().strip()
    asset_type = st.selectbox("자산 종류", ["Stock", "ETF", "Crypto", "Cash"])
    quantity = st.number_input("보유 수량", min_value=0.0, format="%.6f")
    avg_cost = st.number_input("평단가 (매수 통화 기준)", min_value=0.0, format="%.2f")
    
    submitted = st.form_submit_button("자산 추가")
    if submitted and ticker and quantity > 0:
        manager.add_asset(ticker, quantity, avg_cost, asset_type)
        st.sidebar.success(f"{ticker} 추가 완료!")
        # 즉시 새로고침하여 데이터 반영
        st.rerun()

# --- 사이드바: 자산 삭제 ---
st.sidebar.header("🗑️ 자산 삭제")
portfolio_list = manager.get_portfolio()
if portfolio_list:
    tickers = [item['ticker'] for item in portfolio_list]
    to_delete = st.sidebar.selectbox("삭제할 종목 선택", ["선택 안 함"] + tickers)
    if to_delete != "선택 안 함":
        if st.sidebar.button("삭제 확인"):
            manager.remove_asset(to_delete)
            st.success(f"{to_delete} 삭제 완료!")
            st.rerun()

# --- 메인 화면 ---
st.title("💰 나의 은퇴 포트폴리오")

if not portfolio_list:
    st.info("👈 왼쪽 사이드바에서 자산을 추가해주세요! (예: AAPL, 005930.KS, BTC-USD)")
else:
    # 1. 데이터 가져오기
    with st.spinner("최신 시장 데이터와 환율을 가져오는 중..."):
        usd_krw = get_usd_krw_rate()
        st.write(f"ℹ️ 현재 환율 (USD/KRW): **{usd_krw:,.2f} 원**")
        
        portfolio_data = []
        total_value_krw = 0
        total_cost_krw = 0
        
        for item in portfolio_list:
            current_price, currency, name = fetch_current_price(item['ticker'])
            
            # 데이터 못 가져왔을 경우 처리
            if current_price is None:
                st.warning(f"⚠️ {item['ticker']} 데이터를 가져오지 못했습니다. (티커 확인 필요)")
                continue
            
            # 가치 계산
            market_value = current_price * item['quantity']
            cost_basis = item['avg_cost'] * item['quantity']
            
            # KRW 환산
            if currency == 'USD':
                market_value_krw = market_value * usd_krw
                cost_basis_krw = cost_basis * usd_krw
                current_price_krw = current_price * usd_krw
                display_currency = "USD"
            else: # KRW
                market_value_krw = market_value
                cost_basis_krw = cost_basis
                current_price_krw = current_price
                display_currency = "KRW"
            
            profit_loss = market_value_krw - cost_basis_krw
            profit_loss_pct = (profit_loss / cost_basis_krw * 100) if cost_basis_krw > 0 else 0
            
            portfolio_data.append({
                "종목명": name,
                "티커": item['ticker'],
                "자산 종류": item['type'],
                "보유 수량": item['quantity'],
                "현재가 (KRW)": current_price_krw,
                "평가 금액 (KRW)": market_value_krw,
                "매수 금액 (KRW)": cost_basis_krw,
                "수익금 (KRW)": profit_loss,
                "수익률 (%)": profit_loss_pct
            })
            
            total_value_krw += market_value_krw
            total_cost_krw += cost_basis_krw

    # 2. 대시보드 표시
    if portfolio_data:
        df = pd.DataFrame(portfolio_data)

        # 상단 핵심 지표
        total_pl = total_value_krw - total_cost_krw
        total_pl_pct = (total_pl / total_cost_krw * 100) if total_cost_krw > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 자산 (Total Assets)", f"{total_value_krw:,.0f} 원")
        col2.metric("총 매수 금액 (Total Cost)", f"{total_cost_krw:,.0f} 원")
        col3.metric("총 수익 (Profit/Loss)", f"{total_pl:,.0f} 원", f"{total_pl_pct:,.2f}%")

        st.divider()

        # 차트 영역
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📊 종목별 비중")
            fig_alloc = px.pie(df, values='평가 금액 (KRW)', names='종목명', hole=0.3)
            st.plotly_chart(fig_alloc, use_container_width=True)

        with col_chart2:
            st.subheader("🍩 자산 유형별 비중")
            fig_type = px.pie(df, values='평가 금액 (KRW)', names='자산 종류', hole=0.3)
            st.plotly_chart(fig_type, use_container_width=True)

        # 상세 테이블
        st.subheader("📋 상세 보유 현황")
        
        # 보기 좋게 포맷팅
        df_display = df.copy()
        df_display['현재가 (KRW)'] = df_display['현재가 (KRW)'].apply(lambda x: f"{x:,.0f} 원")
        df_display['평가 금액 (KRW)'] = df_display['평가 금액 (KRW)'].apply(lambda x: f"{x:,.0f} 원")
        df_display['매수 금액 (KRW)'] = df_display['매수 금액 (KRW)'].apply(lambda x: f"{x:,.0f} 원")
        df_display['수익금 (KRW)'] = df_display['수익금 (KRW)'].apply(lambda x: f"{x:,.0f} 원")
        df_display['수익률 (%)'] = df_display['수익률 (%)'].apply(lambda x: f"{x:,.2f}%")
        
        st.dataframe(df_display, use_container_width=True)