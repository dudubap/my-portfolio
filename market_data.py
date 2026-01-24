import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def get_usd_krw_rate():
    try:
        ticker = yf.Ticker("KRW=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
        return 1450.0 
    except:
        return 1450.0

@st.cache_data(ttl=600)
def fetch_current_price(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        h = t.history(period="1d")
        if h.empty: return None, "KRW", ticker_symbol
        
        price = h['Close'].iloc[-1]
        currency = t.info.get('currency', 'KRW')
        name = t.info.get('shortName', ticker_symbol)
        
        if ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ"):
            currency = "KRW"
            
        return price, currency, name
    except:
        return None, "KRW", ticker_symbol

@st.cache_data(ttl=86400)
def fetch_dividend_info(ticker_symbol):
    """
    배당률 오류 방지 (30% 이상은 0으로 처리)
    """
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info
        
        # --- [1] 배당률 계산 ---
        yield_pct = 0.0
        
        # 방식 A: 배당금 액수(Rate)로 직접 계산 (제일 정확)
        current_price = info.get('currentPrice') or info.get('previousClose')
        div_rate = info.get('dividendRate')
        
        if div_rate and current_price:
            yield_pct = (div_rate / current_price) * 100
        
        # 방식 B: Trailing Annual (ETF용)
        elif info.get('trailingAnnualDividendRate') and current_price:
            yield_pct = (info.get('trailingAnnualDividendRate') / current_price) * 100
            
        # 방식 C: 야후가 주는 Yield 그대로 사용
        elif info.get('dividendYield'):
            yield_pct = info.get('dividendYield') * 100

        # 🚨 [안전장치] 배당률이 30% 넘으면 데이터 오류로 간주하고 0 처리
        if yield_pct > 30.0:
            yield_pct = 0.0

        # --- [2] 성장률 계산 ---
        growth_rate = 0.0
        try:
            divs = t.dividends
            if len(divs) > 0:
                annual = divs.resample('Y').sum()
                if len(annual) >= 4:
                    last = annual.iloc[-2] # 작년 확정치
                    past = annual.iloc[-6] if len(annual) >= 6 else annual.iloc[0]
                    if past > 0 and last > 0:
                        years = len(annual) - 2 if len(annual) < 6 else 4
                        growth_rate = ((last / past) ** (1/years) - 1) * 100
        except:
            growth_rate = 0.0
            
        return yield_pct, growth_rate

    except:
        return 0.0, 0.0
