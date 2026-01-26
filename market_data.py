import yfinance as yf
import streamlit as st
import time

# 환율 가져오기 (실패시 재시도)
@st.cache_data(ttl=3600)
def get_usd_krw_rate():
    # 3번 시도해봄
    for _ in range(3):
        try:
            ticker = yf.Ticker("KRW=X")
            hist = ticker.history(period="1d")
            if not hist.empty:
                return hist['Close'].iloc[-1]
            time.sleep(0.5) # 0.5초 쉬고 다시 시도
        except:
            pass
    return 1450.0 # 정 안되면 기본값 반환

# 주가 가져오기 (실패시 재시도)
@st.cache_data(ttl=600)
def fetch_current_price(ticker_symbol):
    # 3번 시도 (끈질기게!)
    for _ in range(3):
        try:
            t = yf.Ticker(ticker_symbol)
            h = t.history(period="1d")
            
            if not h.empty:
                price = h['Close'].iloc[-1]
                
                # 통화 확인 logic
                if ticker_symbol.upper().endswith(".KS") or ticker_symbol.upper().endswith(".KQ"):
                    currency = "KRW"
                else:
                    currency = t.info.get('currency', 'USD')
                
                name = t.info.get('shortName', ticker_symbol)
                return price, currency, name
            
            time.sleep(0.2) # 실패하면 잠깐 숨고르기
        except:
            pass
            
    # 3번 다 실패하면 어쩔 수 없이 0 반환
    return None, "KRW", ticker_symbol

# 시장 지수 가져오기
@st.cache_data(ttl=600)
def get_market_indices():
    tickers = {
        "💸 환율": "KRW=X",
        "🇰🇷 코스피": "^KS11",
        "🇺🇸 S&P500": "^GSPC",
        "🇺🇸 나스닥": "^IXIC",
        "😨 VIX (공포)": "^VIX"
    }
    
    data = {}
    
    for name, symbol in tickers.items():
        success = False
        for _ in range(2): # 지수는 2번만 시도
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period="5d")
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = current - prev
                    pct = (change / prev) * 100
                    data[name] = (current, change, pct)
                    success = True
                    break
            except:
                time.sleep(0.2)
        
        if not success:
            data[name] = (0, 0, 0)
            
    return data
