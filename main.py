import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate, fetch_dividend_info
import time

st.set_page_config(page_title="은퇴 포트폴리오 30억 플랜", layout="wide")

try:
    manager = PortfolioManager()
except Exception as e:
    st.stop()

# --- 사이드바 ---
st.sidebar.header("⚙️ 포트폴리오 관리")
tab1, tab2 = st.sidebar.tabs(["➕ 신규 등록", "📝 수정/추매"])

# [Tab 1] 신규 등록 (수동 입력칸 부활)
with tab1:
    with st.form("add_new"):
        st.caption("배당률에 '0'을 입력하면 자동으로 찾습니다.")
        new_ticker = st.text_input("종목 코드").upper().strip()
        new_type = st.selectbox("종류", ["Stock", "ETF", "Crypto", "Cash"])
        new_qty = st.number_input("수량", min_value=0.0, format="%.6f")
        new_cost = st.number_input("평단가", min_value=0.0, format="%.2f")
        # 수동 입력칸
        new_div = st.number_input("배당률 (수동 입력)", min_value=0.0, value=0.0, step=0.1, help="0으로 두면 자동 조회, 입력하면 그 값으로 고정됨")
        
        if st.form_submit_button("신규 등록"):
            if new_ticker and new_qty > 0:
                with st.spinner("저장 중..."):
                    manager.add_asset(new_ticker, new_qty, new_cost, new_type, new_div)
                time.sleep(1)
                st.rerun()

# [Tab 2] 수정/추매
with tab2:
    portfolio = manager.get_portfolio()
    if portfolio:
        tickers = [item['ticker'] for item in portfolio]
        selected_ticker = st.selectbox("종목 선택", tickers)
        cur_asset = next(i for i in portfolio if i['ticker'] == selected_ticker)
        
        # 저장된 배당률 표시
        saved_div = cur_asset.get('dividend_yield', 0.0)
        div_msg = f"{saved_div}% (수동)" if saved_div > 0 else "자동 조회 중"
        
        st.info(f"📊 보유: {cur_asset['quantity']:,.2f}주 / 설정된 배당률: {div_msg}")
        
        edit_mode = st.radio("작업", ["추가 매수", "정보 수정"])
        
        with st.form("edit"):
            if edit_mode == "추가 매수":
                add_q = st.number_input("추가 수량", min_value=0.0)
                add_p = st.number_input("매수 가격", min_value=0.0)
                # 계산 로직
                org_q, org_c = cur_asset['quantity'], cur_asset['avg_cost']
                final_q = org_q + add_q
                final_c = ((org_q*org_c)+(add_q*add_p))/final_q if final_q>0 else org_c
                final_div = saved_div # 기존 배당 설정 유지
            else:
                final_q = st.number_input("총 수량", value=float(cur_asset['quantity']))
                final_c = st.number_input("총 평단가", value=float(cur_asset['avg_cost']))
                final_div = st.number_input("배당률 수정 (0=자동)", value=float(saved_div))

            if st.form_submit_button("적용"):
                manager.add_asset(selected_ticker, final_q, final_c, cur_asset['type'], final_div)
                st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 새로고침"): st.rerun()

# --- 메인 화면 ---
st.header("🎯 은퇴 목표 (30억 플랜)")
c1, c2, c3 = st.columns(3)
target = c1.number_input("목표 금액", value=3000000000, step=100000000, format="%d")
month_inv = c2.number_input("월 투자금", value=2000000, step=100000)
rate = c3.slider("목표 수익률", 0.0, 30.0, 8.0)
st.title("🚀 나의 은퇴 현황판")

if portfolio:
    with st.spinner("데이터 분석 중..."):
        usd = get_usd_krw_rate()
        st.caption(f"환율: 1 USD = {usd:,.2f} KRW")
        data = []
        tot_val = 0
        tot_inv = 0
        tot_div = 0
        
        for item in portfolio:
            p, cur, name = fetch_current_price(item['ticker'])
            if p is None: p, name, cur = 0, item['ticker'], "KRW"
            
            # [핵심 로직] 수동 vs 자동 우선순위 결정
            saved_yield = item.get('dividend_yield', 0.0)
            auto_yield, growth = fetch_dividend_info(item['ticker'])
            
            # 수동 입력값이 0보다 크면 그걸 쓰고, 아니면 자동값 사용
            if saved_yield > 0:
                final_yield = saved_yield
                is_manual = True
            else:
                final_yield = auto_yield
                is_manual = False
            
            mul = usd if cur == 'USD' else 1
            val = p * item['quantity'] * mul
            cost = item['avg_cost'] * item['quantity'] * mul
            
            # 예상 배당금
            an_div = val * (final_yield / 100)
            
            # 배당률 표시 문자열
            yield_str = f"{final_yield:.2f}%"
            if is_manual: yield_str += " (수동)"
            
            # 성장률 표시
            g_str = f"{growth:.1f}%"
            if growth > 10: g_str += " 🔥"
            elif growth < 0: g_str += " 📉"

            data.append({
                "종목": name, "티커": item['ticker'], "종류": item['type'],
                "수량": item['quantity'], "현재가": p*mul, "잔고": val,
                "수익률": ((val-cost)/cost*100) if cost>0 else 0,
                "배당률": yield_str, "배당성장": g_str, "연 배당금": an_div
            })
            tot_val += val; tot_inv += cost; tot_div += an_div

        if tot_val > 0: manager.update_history(tot_val)

    # UI 표시
    prog = min(tot_val/target, 1.0)
    st.write(f"### 🚩 달성률: **{prog*100:.2f}%**")
    st.progress(prog)
    
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 자산", f"{tot_val:,.0f}")
    c2.metric("총 수익", f"{tot_val-tot_inv:,.0f}", f"{(tot_val-tot_inv)/tot_inv*100:.2f}%")
    c3.metric("연 배당금", f"{tot_div:,.0f}", f"{tot_div/tot_val*100:.2f}%")
    c4.metric("월 현금흐름", f"{tot_div/12:,.0f}")
    
    st.divider()
    c1, c2 = st.columns(2)
    hist = pd.DataFrame(manager.get_history())
    if not hist.empty:
        c1.plotly_chart(px.line(hist, x='date', y='value', title="자산 성장"), use_container_width=True)
    
    df = pd.DataFrame(data)
    div_df = df[df['연 배당금'] > 0]
    if not div_df.empty:
        c2.plotly_chart(px.pie(div_df, values='연 배당금', names='종목', title="배당 비중", hole=0.4), use_container_width=True)
    
    st.subheader("📋 상세 현황")
    df_show = df.copy()
    for c in ['현재가', '잔고', '연 배당금']: df_show[c] = df_show[c].apply(lambda x: f"{x:,.0f} 원")
    df_show['수익률'] = df_show['수익률'].apply(lambda x: f"{x:,.2f}%")
    st.dataframe(df_show[['종목', '수량', '잔고', '수익률', '배당률', '배당성장', '연 배당금']], use_container_width=True, hide_index=True)
