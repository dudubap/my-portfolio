import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
# fetch_dividend_info 함수가 추가되었습니다.
from market_data import fetch_current_price, get_usd_krw_rate, fetch_dividend_info
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

# 탭 나누기
tab1, tab2 = st.sidebar.tabs(["➕ 신규 등록", "📝 수정/추매"])

# [Tab 1] 신규 등록 (배당률 입력칸 삭제됨 - 자동 조회)
with tab1:
    st.subheader("새로운 종목 추가")
    with st.form("add_new"):
        st.caption("배당률은 자동으로 가져옵니다! 🤖")
        new_ticker = st.text_input("종목 코드 (예: SCHD, O, 005930.KS)").upper().strip()
        new_type = st.selectbox("종류", ["Stock", "ETF", "Crypto", "Cash"])
        new_qty = st.number_input("수량", min_value=0.0, format="%.6f")
        new_cost = st.number_input("평단가", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("신규 등록"):
            if new_ticker and new_qty > 0:
                with st.spinner("배당 정보 조회 및 저장 중..."):
                    # 배당률은 0으로 저장하고, 화면 보여줄 때 실시간 조회함
                    manager.add_asset(new_ticker, new_qty, new_cost, new_type, 0.0)
                time.sleep(1)
                st.rerun()

# [Tab 2] 수정/추매 (여기도 배당률 입력 삭제)
with tab2:
    st.subheader("기존 자산 수정 / 추가 매수")
    portfolio = manager.get_portfolio()
    
    if not portfolio:
        st.info("자산을 먼저 추가하세요.")
    else:
        tickers = [item['ticker'] for item in portfolio]
        selected_ticker = st.selectbox("종목 선택", tickers)
        
        current_asset = next(item for item in portfolio if item['ticker'] == selected_ticker)
        cur_qty = current_asset['quantity']
        cur_cost = current_asset['avg_cost']
        
        st.info(f"📊 보유: {cur_qty:,.2f}주 / 평단: {cur_cost:,.0f}원")
        
        edit_mode = st.radio("작업 선택", ["추가 매수 (물타기)", "수량/평단 직접 수정"])
        
        with st.form("update_existing"):
            if edit_mode == "추가 매수 (물타기)":
                added_qty = st.number_input("추가 수량 (+)", min_value=0.0, format="%.6f")
                added_price = st.number_input("매수 가격", min_value=0.0, format="%.2f")
                
                new_total_qty = cur_qty + added_qty
                if new_total_qty > 0:
                    new_avg_cost = ((cur_qty * cur_cost) + (added_qty * added_price)) / new_total_qty
                else:
                    new_avg_cost = cur_cost
                    
            else: # 직접 수정
                new_total_qty = st.number_input("총 수량", value=float(cur_qty), format="%.6f")
                new_avg_cost = st.number_input("총 평단가", value=float(cur_cost), format="%.2f")

            if st.form_submit_button("업데이트"):
                with st.spinner("저장 중..."):
                    manager.add_asset(selected_ticker, new_total_qty, new_avg_cost, current_asset['type'], 0.0)
                time.sleep(1)
                st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 새로고침"):
    st.rerun()

# --- 메인 화면 ---
st.header("🎯 은퇴 목표 (30억 플랜)")
c1, c2, c3 = st.columns(3)
target_asset = c1.number_input("목표 금액", value=3000000000, step=100000000, format="%d")
monthly_input = c2.number_input("월 투자금", value=2000000, step=100000, format="%d")
exp_return_rate = c3.slider("목표 수익률(%)", 0.0, 30.0, 8.0)

st.title("🚀 나의 은퇴 현황판 (Goal: 30억)")

if not portfolio:
    st.info("👈 사이드바에서 자산을 추가해주세요. 배당률은 알아서 찾아옵니다!")
else:
    with st.spinner("가격, 환율, 그리고 배당 성장률 분석 중... 🕵️"):
        usd = get_usd_krw_rate()
        st.caption(f"환율: 1 USD = {usd:,.2f} KRW")
        
        data = []
        total_val = 0
        total_inv = 0
        total_annual_div = 0
        
        for item in portfolio:
            # 1. 가격 정보
            p, cur, name = fetch_current_price(item['ticker'])
            if p is None: p, name, cur = 0, item['ticker'], "KRW"
            
            # 2. 배당 정보 (자동 조회!)
            # yield_pct: 배당률, growth_rate: 5년 성장률
            yield_pct, growth_rate = fetch_dividend_info(item['ticker'])
            
            multiplier = usd if cur == 'USD' else 1
            val = p * item['quantity'] * multiplier
            cost = item['avg_cost'] * item['quantity'] * multiplier
            current_p_krw = p * multiplier
            
            # 예상 연 배당금
            annual_div = val * (yield_pct / 100)
            
            # 성장률 뱃지 만들기
            growth_str = f"{growth_rate:.1f}%"
            if growth_rate > 10:
                growth_str += " 🔥" # 고성장
            elif growth_rate > 0:
                growth_str += " 📈" # 성장 중
            elif growth_rate < 0:
                growth_str += " 📉" # 감소 중 (조심!)
            
            data.append({
                "종목": name, "티커": item['ticker'], "종류": item['type'],
                "수량": item['quantity'], "현재가": current_p_krw,
                "잔고": val, "원금": cost, "수익": val - cost,
                "수익률": ((val-cost)/cost*100) if cost>0 else 0,
                "배당률": yield_pct, 
                "연 배당금": annual_div,
                "배당성장(5년)": growth_str # 표에 보여줄 문자열
            })
            total_val += val
            total_inv += cost
            total_annual_div += annual_div

        if total_val > 0:
            manager.update_history(total_val)

    if total_val > 0:
        # 목표 달성률 & 시뮬레이션
        progress = min(total_val / target_asset, 1.0)
        st.write(f"### 🚩 30억 달성률: **{progress*100:.2f}%** (목표: {target_asset:,.0f} 원)")
        st.progress(progress)
        
        if monthly_input > 0 and total_val < target_asset:
            r = exp_return_rate / 100 / 12
            current = total_val
            months = 0
            while current < target_asset and months < 600:
                current = current * (1 + r) + monthly_input
                months += 1
            years, remain = months // 12, months % 12
            st.info(f"💡 월 **{monthly_input:,.0f}원** 투자 시, **{years}년 {remain}개월 뒤** 30억 달성 가능!")

        st.divider()

        # 지표 (4단)
        monthly_div = total_annual_div / 12
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 자산", f"{total_val:,.0f} 원")
        c2.metric("총 수익", f"{total_val-total_inv:,.0f} 원", f"{(total_val-total_inv)/total_inv*100:.2f}%")
        c3.metric("연 예상 배당금", f"{total_annual_div:,.0f} 원", f"평균 배당률 {total_annual_div/total_val*100:.2f}%")
        c4.metric("월 현금흐름", f"{monthly_div:,.0f} 원", "Passive Income")
        
        st.divider()

        # 차트
        st.subheader("📈 자산 성장 & 배당 분석")
        
        c1, c2 = st.columns(2)
        history_data = manager.get_history()
        with c1:
             # 성장 그래프
            if len(history_data) > 0:
                df_hist = pd.DataFrame(history_data)
                df_hist['date'] = pd.to_datetime(df_hist['date'])
                fig_hist = px.line(df_hist, x='date', y='value', markers=True, title="자산 성장 추이")
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("데이터가 쌓이면 그래프가 나타납니다.")

        df = pd.DataFrame(data)
        with c2:
            # 배당금 파이 차트
            div_df = df[df['연 배당금'] > 0]
            if not div_df.empty:
                fig_div = px.pie(div_df, values='연 배당금', names='종목', title="내 월급(배당)은 어디서 나올까?", hole=0.4)
                st.plotly_chart(fig_div, use_container_width=True)
            else:
                st.warning("배당주가 아직 없습니다.")

        # 상세 표 (배당 성장률 컬럼 추가됨!)
        st.subheader("📋 포트폴리오 상세 (배당 성장 분석)")
        df_display = df.copy()
        for col in ['현재가', '잔고', '원금', '수익', '연 배당금']:
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f} 원")
        df_display['수익률'] = df_display['수익률'].apply(lambda x: f"{x:,.2f}%")
        df_display['배당률'] = df_display['배당률'].apply(lambda x: f"{x:,.2f}%")
        
        # 컬럼 순서 조정해서 보여주기
        st.dataframe(
            df_display[['종목', '티커', '수량', '잔고', '수익률', '배당률', '배당성장(5년)', '연 배당금']], 
            use_container_width=True, 
            hide_index=True
        )
