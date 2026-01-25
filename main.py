import streamlit as st
import pandas as pd
import plotly.express as px
from portfolio_manager import PortfolioManager
from market_data import fetch_current_price, get_usd_krw_rate, get_market_indices
import time

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
if st.sidebar.button("🔄 새로고침"): st.rerun()

# --- 메인 화면 ---
target = 3000000000
month_inv = 2000000
rate = 8.0

st.title("🚀 나의 은퇴 현황판 (Goal: 30억)")

# [시장 지수 전광판]
indices = get_market_indices()
m1, m2, m3, m4, m5 = st.columns(5)

val, chg, pct = indices["💸 환율"]
m1.metric("💸 환율", f"{val:,.0f}원", f"{chg:.1f}원")

val, chg, pct = indices["🇰🇷 코스피"]
m2.metric("🇰🇷 코스피", f"{val:,.0f}", f"{chg:.0f} ({pct:.1f}%)")

val, chg, pct = indices["🇺🇸 S&P500"]
m3.metric("🇺🇸 S&P500", f"{val:,.0f}", f"{chg:.0f} ({pct:.1f}%)")

val, chg, pct = indices["🇺🇸 나스닥"]
m4.metric("🇺🇸 나스닥", f"{val:,.0f}", f"{chg:.0f} ({pct:.1f}%)")

val, chg, pct = indices["😨 VIX (공포)"]
m5.metric("😨 VIX 지수", f"{val:,.2f}", f"{chg:.2f}", delta_color="inverse")

st.divider()

if portfolio:
    with st.spinner("자산 가치 계산 중..."):
        usd_rate = get_usd_krw_rate()
        
        data = []
        tot_val = 0
        tot_inv = 0
        
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
                "매수통화": my_curr
            })
            tot_val += val_krw
            tot_inv += cost_krw

        if tot_val > 0: manager.update_history(tot_val)

    if tot_val > 0:
        prog = min(tot_val/target, 1.0)
        st.write(f"### 🚩 목표 달성률: **{prog*100:.2f}%** (목표: {target:,.0f} 원)")
        st.progress(prog)
        
        if month_inv > 0 and tot_val < target:
            r = rate / 100 / 12
            current = tot_val
            months = 0
            while current < target and months < 600:
                current = current * (1 + r) + month_inv
                months += 1
            years, remain = months // 12, months % 12
            st.info(f"💡 현재 속도로 투자 시, **{years}년 {remain}개월 뒤** 목표 달성 예상!")

    st.divider()
    
    # 핵심 지표
    c1, c2, c3 = st.columns(3)
    c1.metric("총 자산", f"{tot_val:,.0f} 원")
    c2.metric("총 투자원금", f"{tot_inv:,.0f} 원")
    c3.metric("총 수익", f"{tot_val-tot_inv:,.0f} 원", f"{(tot_val-tot_inv)/tot_inv*100:.2f}%")
    
    st.divider()
    
    # [차트 영역]
    c1, c2 = st.columns([2, 1])
    
    # 1. 주간 성장 차트
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
    
    # 2. 비중 차트
    df = pd.DataFrame(data)
    if not df.empty:
        pie_type = c2.radio("비중 보기 기준", ["종목별", "자산군별 (Stock/ETF)"], horizontal=True)
        
        if pie_type == "종목별":
            fig_pie = px.pie(df, values='평가금액', names='종목', hole=0.5)
        else:
            fig_pie = px.pie(df, values='평가금액', names='종류', hole=0.5)
            
        fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        fig_pie.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
        c2.plotly_chart(fig_pie, use_container_width=True)
    
    # [상세 표]
    st.subheader("📋 상세 현황")
    
    # [핵심] 평가금액 기준 내림차순 정렬 (큰 금액이 위로)
    df_show = df.sort_values(by='평가금액', ascending=False).copy()
    
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_order=["종목", "종류", "수량", "평가금액", "수익", "수익률"], 
        column_config={
            "종목": st.column_config.TextColumn("종목", help="티커명"),
            "종류": st.column_config.TextColumn("Type"),
            "수량": st.column_config.NumberColumn("수량", format="%.2f"),
            "평가금액": st.column_config.NumberColumn("평가액", format="%d 원"),
            "수익": st.column_config.NumberColumn("수익금", format="%d 원"),
            "수익률": st.column_config.NumberColumn("수익률", format="%.2f %%")
        }
    )

    if not df.empty:
        best = df.loc[df['수익'].idxmax()]
        worst = df.loc[df['수익'].idxmin()]
        st.caption(f"👑 Best: **{best['종목']}** (+{best['수익']:,.0f}원)  |  💧 Worst: **{worst['종목']}** ({worst['수익']:,.0f}원)")
