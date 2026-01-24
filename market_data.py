import yfinance as yf
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
    """
    현재가와 '거래 통화(Currency)'를 반환합니다.
    """
    try:
        t = yf.Ticker(ticker_symbol)
        # 1. 가격 가져오기
        h = t.history(period="1d")
        if h.empty: return None, "KRW", ticker_symbol
        
        price = h['Close'].iloc[-1]
        
        # 2. 통화 정보 확인
        # 한국 주식(.KS, .KQ)은 무조건 KRW로 강제 설정 (데이터 오류 방지)
        if ticker_symbol.upper().endswith(".KS") or ticker_symbol.upper().endswith(".KQ"):
            currency = "KRW"
        else:
            currency = t.info.get('currency', 'USD')
            
        name = t.info.get('shortName', ticker_symbol)
            
        return price, currency, name
    except:
        return None, "KRW", ticker_symbol
