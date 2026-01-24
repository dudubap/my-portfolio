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
    try:
        t = yf.Ticker(ticker_symbol)
        h = t.history(period="1d")
        if h.empty: return None, "KRW", ticker_symbol
        
        price = h['Close'].iloc[-1]
        
        # 한국 주식(.KS, .KQ)은 무조건 KRW
        if ticker_symbol.upper().endswith(".KS") or ticker_symbol.upper().endswith(".KQ"):
            currency = "KRW"
        else:
            currency = t.info.get('currency', 'USD')
            
        name = t.info.get('shortName', ticker_symbol)
        return price, currency, name
    except:
        return None, "KRW", ticker_symbol

# [추가됨] 주요 시장 지수 4개 가져오기
@st.cache_data(ttl=600)
def get_market_indices():
    """
    환율, 코스피, S&P500, 나스닥의 현재가와 등락폭을 가져옵니다.
    """
    tickers = {
        "💸 환율 (USD)": "KRW=X",
        "🇰🇷 코스피": "^KS11",
        "🇺🇸 S&P 500": "^GSPC",
        "🇺🇸 나스닥": "^IXIC"
    }
    
    data = {}
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            # 5일치 가져오는 이유: 주말/휴일이 껴있을 때 전일 종가(Close)를 안전하게 찾기 위해
            hist = t.history(period="5d")
            
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]   # 오늘 현재가
                prev = hist['Close'].iloc[-2]      # 어제 종가
                change = current - prev            # 변동액
                pct = (change / prev) * 100        # 변동률(%)
                
                data[name] = (current, change, pct)
            else:
                data[name] = (0, 0, 0)
        except:
            data[name] = (0, 0, 0)
            
    return data
