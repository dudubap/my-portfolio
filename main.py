import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate
import time

# 1. 페이지 설정 (반드시 맨 처음에 있어야 함)
st.set_page_config(page_title="은퇴 포트폴리오 트래커", layout="wide")

# 2. 포트폴리오 매니저 연결 (GitHub)
try:
    manager = PortfolioManager()
except Exception as e:
    st.error(f"GitHub 연결에 실패했습니다. 인터넷 상태나 토큰을 확인하세요.\n에러 내용: {e}")
    st.stop()

# --- 사이드바: 자산 관리 ---
st.sidebar.header("⚙️ 메뉴")

# 새로고침 버튼
if st.sidebar.button("🔄 가격 새로고침"):
    st.rerun()

st.sidebar.divider()

# 자산 추가
st.sidebar.header("➕ 자산 추가")
with st.sidebar.form("add_asset_form"):
    st.caption("예: 삼성전자(005930.KS), AAPL, BTC-USD")
    ticker = st.text_input("종목 코드").upper().strip()
    asset_type = st.selectbox("자산 종류", ["Stock", "ETF", "Crypto", "Cash"])
    quantity = st.number_input("보유 수량", min_value=0.0, format="%.6f")
    avg_cost = st.number_input("평단가 (매수 통화 기준)", min_value=0.0, format="%.2f")
    
    if st.form_submit_button("추가 / 수정"):
        if ticker and quantity > 0:
            with st.spinner("GitHub에 저장 중... (약 2~3초 소요)"):
                manager.add_asset(ticker, quantity, avg_cost, asset_type)
            st.sidebar.success(f"{ticker} 저장 완료!")
            time.sleep(1) # GitHub 반영 대기
            st.rerun()
        else:
            st.sidebar.warning("종목 코드와 수량을 입력해주세요.")

# 자산 삭제
portfolio_list = manager.get_portfolio()
if portfolio_list:
    st.sidebar.header("🗑️ 자산 삭제")
    tickers = [item['ticker'] for item in portfolio_list]
    to_delete = st.sidebar.selectbox("삭제할 종목", ["선택하세요"] + tickers)
    
    if to_delete != "선택하세요":
        if st.sidebar.button("삭제 실행"):
            with st.spinner("삭제 중..."):
                manager.remove_asset(to_delete)
            st.success("삭제 완료!")
            time.sleep(1)
            st.rerun()

# --- 메인 대시보드 화면 ---
st.title("💰 나의 은퇴 포트폴리오")

# 자산이 없을 때 안내
if not portfolio_list:
    st.info("👈 왼쪽 사이드바에서 자산을 추가하면, 여기에 그래프가 나타납니다!")

else:
    # 3. 데이터 계산 로직
    with st.spinner("현재가와 환율을 가져오는 중입니다..."):
        usd_krw = get_usd_krw_rate()
        
        # 환율 표시
        st.markdown(f"**ℹ️ 현재 환율:** `1 USD = {usd_krw:,.2f} KRW`")
        
        portfolio_data = []
        total_value = 0
        total_cost = 0
        
        for item in portfolio_list:
            # 가격 가져오기
            price, currency, name = fetch_current_price(item['ticker'])
            
            # 가격 못 가져왔을 때 처리 (그래프 깨짐 방지)
            if price is None:
                price = 0
                name = item['ticker'] + " (가격 확인 불가)"
                currency = "KRW"
            
            # 가치 계산
            val = price * item['quantity']
            cost = item['avg_cost'] * item['quantity']
            
            # 원화 환산
            if currency == 'USD':
                val_krw = val * usd_krw
                cost_krw = cost * usd_krw
                price_krw = price * usd_krw
            else:
                val_krw = val
                cost_krw = cost
                price_krw = price
            
            # 수익 계산
            profit = val_krw - cost_krw
            profit_pct = (profit / cost_krw * 100) if cost_krw > 0 else 0
            
            portfolio_data.append({
                "종목명": name,
                "티커": item['ticker'],
                "자산 종류": item['type'],
                "보유 수량": item['quantity'],
                "평가 금액": val_krw,     # 차트용
                "매수 금액": cost_krw,
                "수익금": profit,
                "수익률": profit_pct,
                "현재가": price_krw
            })
            
            total_value += val_krw
            total_cost += cost_krw

    # 4. 결과 출력 (DataFrame 생성)
    if portfolio_data:
        df = pd.DataFrame(portfolio_data)

        # (1) 핵심 지표 (3단 컬럼)
        total_profit = total_value - total_cost
        total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 자산", f"{total_value:,.0f} 원")
        col2.metric("총 투자 원금", f"{total_cost:,.0f} 원")
        col3.metric("총 수익", f"{total_profit:,.0f} 원", f"{total_profit_pct:,.2f}%")

        st.divider()

        # (2) 차트 영역 (여기가 안 보였던 부분)
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📊 종목별 비중")
            # 데이터가 있어야 차트를 그림
            if total_value > 0:
                fig1 = px.pie(df, values='평가 금액', names='종목명', hole=0.4)
                fig1.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("자산 가치가 0원이라 차트를 그릴 수 없습니다.")

        with c2:
            st.subheader("🍩 자산 종류별 비중")
            if total_value > 0:
                fig2 = px.pie(df, values='평가 금액', names='자산 종류', hole=0.4)
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("자산 가치가 0원이라 차트를 그릴 수 없습니다.")

        # (3) 상세 표
        st.subheader("📋 상세 자산 현황")
        
        # 표 예쁘게 꾸미기
        df_show = df.copy()
        for c in ['평가 금액', '매수 금액', '수익금', '현재가']:
            df_show[c] = df_show[c].apply(lambda x: f"{x:,.0f} 원")
        df_show['수익률'] = df_show['수익률'].apply(lambda x: f"{x:,.2f}%")
        
        st.dataframe(
            df_show[['종목명', '티커', '보유 수량', '현재가', '평가 금액', '수익금', '수익률']], 
            use_container_width=True,
            hide_index=True
        )
