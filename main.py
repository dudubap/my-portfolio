import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate, get_market_indices
import time

# ==========================================
# 💰 [설정] 나만의 배당률표 (수동 관리)
# yfinance가 불안정하므로, 여기에 '연 배당률(%)'을 직접 적어두는 게 가장 확실합니다.
# 없는 종목은 기본값(1.5%)으로 계산됩니다.
# ==========================================
MY_DIVIDEND_RATES = {
    # [미국 고배당 & 채권]
    "JEPQ": 9.5,   # 커버드콜
    "JEPI": 7.5,
    "O": 5.2,      # 리얼티인컴 (월배당)
    "SCHD": 3.4,   # 배당성장
    "VNQ": 3.0,    # 부동산
    "TMF": 3.2,    # 채권 3배
    "TLT": 3.8,    # 채권
    
    # [미국 우량주 & 지수]
    "VOO": 1.3,    # S&P500
    "SPY": 1.3,
    "QQQ": 0.6,
    "QLD": 0.3,    # 나스닥 2배
    "NVDA": 0.03,  # 거의 없음
    "MSFT": 0.7,
    "AAPL": 0.5,
    "KO": 3.1,     # 코카콜라
    
    # [한국 ETF 예시]
    "360750.KS": 3.5, # TIGER 미국배당다우존스
    "005930.KS": 2.0, # 삼성전자
}
# ==========================================

st.set_page_config(page_title="은퇴 포트폴리오 30억 플랜", layout="wide")

try:
    manager = PortfolioManager()
except Exception as e:
    st.error(f"데이터 매니저 로딩 실패: {e}")
    st.stop()

# --- 사이드바 ---
st.sidebar.header("⚙️ 자산 관리")
tab1, tab2 = st.sidebar.tabs(["➕ 신규 등록", "📝 매수/매도/수정"])

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

# [Tab 2] 매수/매도/수정
with tab2:
    portfolio = manager.get_portfolio()
    if portfolio:
        tickers = [item['ticker'] for item in portfolio]
        selected_ticker = st.selectbox("종목 선택", tickers)
        cur_asset = next(i for i in portfolio if i['ticker'] == selected_ticker)
        
        asset_curr = cur_asset.get('currency', 'USD')
        symbol = "₩" if asset_curr == 'KRW' else "$"
        
        st.info(f"📊 보유: {cur_asset['quantity']:,.2f}주 / 평단: {symbol}{cur_asset['avg_cost']:,.2f}")
        
        edit_mode = st.radio("작업 선택", ["📈 추가 매수", "📉 부분 매도", "📝 정보 수정"])
        
        with st.form("edit"):
            if edit_mode.startswith("📈"):
                add_q = st.number_input("추가 매수 수량 (+)", min_value=0.0, format="%.6f")
                add_p = st.number_input("매수 단가", min_value=0.0, format="%.2f")
                org_q, org_c = cur_asset['quantity'], cur_asset['avg_cost']
                final_q = org_q + add_q
                final_c = ((org_q*org_c)+(add_q*add_p))/final_q if final_q>0 else org_c
                final_curr = asset_curr
            
            elif edit_mode.startswith("📉"):
                sell_q = st.number_input("매도 수량 (-)", min_value=0.0, max_value=float(cur_asset['quantity']), format="%.6f")
                org_q, org_c = cur_asset['quantity'], cur_asset['avg_cost']
                final_q = org_q - sell_q
                final_c = org_c 
                final_curr = asset_curr
                if final_q == 0: st.warning("⚠️ 전량 매도 (삭제됨)")

            else:
                final_q = st.number_input("총 수량", value=float(cur_asset['quantity']))
                final_c = st.number_input("총 평단가", value=float(cur_asset['avg_cost']))
                curr_idx = 0 if asset_curr == 'USD' else 1
                new_curr_str = st.radio("통화 변경", ["USD", "KRW"], index=curr_idx, horizontal=True)
                final_curr = new_curr_str

            if st.form_submit_button("적용하기"):
                with st.spinner("처리 중..."):
                    manager.add_asset(selected_ticker, final_q, final_c, cur_asset['type'], final_curr)
                time.sleep(1)
                st.rerun()

st.sidebar.divider()
with st.sidebar.expander("🗑️ 자산 아예 삭제하기"):
    if portfolio:
        del_ticker = st.selectbox("삭제할 종목", ["선택"] + tickers)
        if del_ticker != "선택" and st.button("❌ 삭제 실행"):
            manager.remove_asset(del_ticker)
            st.rerun()

st.sidebar.divider()
st.sidebar.caption("🔧 시뮬레이션 설정")
rate = st.sidebar.slider("연 목표 수익률 (%)", 1.0, 20.0, 8.0, step=0.5)
month_inv = 2000000
target = 3000000000 

if st.sidebar.button("🔄 새로고침"): st.rerun()

# --- 메인 화면 ---
st.title("🚀 나의 은퇴 현황판 (Goal: 30억)")

# [시장 지수 전광판]
indices = get_market_indices()
m1, m2, m3, m4, m5 = st.columns(5)
idx_list = ["💸 환율", "🇰🇷 코스피", "🇺🇸 S&P500", "🇺🇸 나스닥", "😨 VIX (공포)"]
for col, name in zip([m1, m2, m3, m4, m5], idx_list):
    val, chg, pct = indices[name]
    color = "inverse" if "VIX" in name else "normal"
    col.metric(name, f"{val:,.2f}", f"{chg:.2f} ({pct:.1f}%)", delta_color=color)

st.divider()

if portfolio:
    with st.spinner("자산 가치 & 배당금 계산 중..."):
        usd_rate = get_usd_krw_rate()
        
        data = []
        tot_val = 0
        tot_inv = 0
        tot_month_div = 0 # 월 배당금 합계
        
        for item in portfolio:
            p, market_curr, name = fetch_current_price(item['ticker'])
            if p is None: p, name, market_curr = 0, item['ticker'], "KRW"
            
            my_curr = item.get('currency', 'USD')
            
            # (A) 평가 금액
            if market_curr == 'USD':
                val_krw = p * item['quantity'] * usd_rate
                current_price_krw = p * usd_rate
            else:
                val_krw = p * item['quantity']
                current_price_krw = p
            
            # (B) 매수 금액
            if my_curr == 'USD':
                cost_krw = item['avg_cost'] * item['quantity'] * usd_rate
            else:
                cost_krw = item['avg_cost'] * item['quantity']
            
            # (C) 배당금 계산 (새로 추가된 로직!)
            # 딕셔너리에서 찾고, 없으면 기본값 1.5% 적용
            div_yield = MY_DIVIDEND_RATES.get(item['ticker'], 1.5)
            year_div_krw = val_krw * (div_yield / 100) # 연 배당금
            month_div_krw = year_div_krw / 12          # 월 배당금
            
            # 수익률
            if cost_krw > 0:
                roi = ((val_krw - cost_krw) / cost_krw) * 100 
            else:
                roi = 0
            
            data.append({
                "종목": name, 
                "티커": item['ticker'], 
                "종류": item['type'],
                "수량": item['quantity'], 
                "현재가(KRW)": current_price_krw, 
                "평가금액": val_krw, 
                "매수금액": cost_krw, 
                "수익": val_krw - cost_krw,
                "수익률": roi,
                "예상월배당": month_div_krw, # 표에 표시하기 위해 저장
                "배당률(%)": div_yield
            })
            tot_val += val_krw
            tot_inv += cost_krw
            tot_month_div += month_div_krw

        if tot_val > 0: 
            manager.update_history(tot_val)

    # 1. 목표 달성률
    if tot_val > 0:
        prog = min(tot_val/target, 1.0)
        st.write(f"### 🚩 목표 달성률: **{prog*100:.2f}%** (목표: {target:,.0f} 원)")
        st.progress(prog)
    
    st.divider()
    
    # 2. 핵심 지표 & 배당 현금 흐름 (NEW!)
    c1, c2, c3 = st.columns(3)
    c1.metric("총 자산", f"{tot_val:,.0f} 원")
    c2.metric("총 수익", f"{tot_val-tot_inv:,.0f} 원", f"{(tot_val-tot_inv)/tot_inv*100:.2f}%")
    
    # [치킨 지수 로직 적용] 🍗
    chicken_count = tot_month_div / 20000 # 치킨 1마리 2만원 가정
    c3.metric("💰 월 예상 배당금", f"{tot_month_div:,.0f} 원", f"치킨 {chicken_count:.1f}마리 가능 🍗")
    
    st.divider()
    
    # [차트 영역]
    c1, c2 = st.columns([2, 1])
    
    # 성장 차트
    hist_list = manager.get_history()
    if len(hist_list) > 0:
        df_hist = pd.DataFrame(hist_list)
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        df_hist['week_id'] = df_hist['date'].dt.strftime('%Y-%W')
        df_weekly = df_hist.sort_values('date').groupby('week_id').tail(1)
        df_weekly['display_date'] = df_weekly['date'].dt.strftime('%m-%d')
        
        fig = px.line(df_weekly, x='display_date', y='value', markers=True, title="📈 자산 성장 (주간)")
        fig.update_yaxes(range=[0, target * 1.1], showticklabels=False, showgrid=False, title=None)
        fig.update_xaxes(title=None, type='category')
        fig.add_hline(y=target, line_dash="dot", line_color="#2ECC71", annotation_text="🏁 Goal")
        fig.update_traces(line_color='#FF4B4B', hovertemplate='<b>%{x}</b><br>자산: %{y:,.0f} 원<extra></extra>')
        c1.plotly_chart(fig, use_container_width=True)
    else:
        c1.info("데이터가 없습니다.")
    
    # 비중 차트
    df = pd.DataFrame(data)
    if not df.empty:
        pie_type = c2.radio("비중 보기 기준", ["종목별", "자산군별 (Stock/ETF)"], horizontal=True)
        col_name = '종목' if pie_type == "종목별" else '종류'
        fig_pie = px.pie(df, values='평가금액', names=col_name, hole=0.5)
        fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        fig_pie.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
        c2.plotly_chart(fig_pie, use_container_width=True)
    
    # [상세 표] 배당 정보 추가
    st.subheader("📋 상세 현황 (배당 포함)")
    df_show = df.sort_values(by='평가금액', ascending=False).copy()
    
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_order=["종목", "수량", "평가금액", "수익률", "배당률(%)", "예상월배당"], # 컬럼 순서
        column_config={
            "종목": st.column_config.TextColumn("종목", help="티커명"),
            "수량": st.column_config.NumberColumn("수량", format="%.2f"),
            "평가금액": st.column_config.NumberColumn("평가액", format="%d 원"),
            "수익률": st.column_config.NumberColumn("수익률", format="%.2f %%"),
            "배당률(%)": st.column_config.NumberColumn("배당률", format="%.1f %%"), # 내가 입력한 배당률
            "예상월배당": st.column_config.NumberColumn("월 배당(예상)", format="%d 원"), # 계산된 월 현금
        }
    )

    if not df.empty:
        best = df.loc[df['수익'].idxmax()]
        st.caption(f"👑 Best: **{best['종목']}** (+{best['수익']:,.0f}원)")
