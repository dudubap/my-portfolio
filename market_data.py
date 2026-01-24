# market_data.py 전체를 이걸로 덮어씌우세요 (VIX 추가됨)
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
        
        if ticker_symbol.upper().endswith(".KS") or ticker_symbol.upper().endswith(".KQ"):
            currency = "KRW"
        else:
            currency = t.info.get('currency', 'USD')
            
        name = t.info.get('shortName', ticker_symbol)
        return price, currency, name
    except:
        return None, "KRW", ticker_symbol

@st.cache_data(ttl=600)
def get_market_indices():
    """
    주요 지수 + VIX(공포지수) 가져오기
    """
    tickers = {
        "💸 환율": "KRW=X",
        "🇰🇷 코스피": "^KS11",
        "🇺🇸 S&P500": "^GSPC",
        "🇺🇸 나스닥": "^IXIC",
        "😨 VIX (공포)": "^VIX"  # [추가됨] 월가 공포지수
    }
    
    data = {}
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = current - prev
                pct = (change / prev) * 100
                data[name] = (current, change, pct)
            else:
                data[name] = (0, 0, 0)
        except:
            data[name] = (0, 0, 0)
            
    return data
