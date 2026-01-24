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
        return 1450.0 # 에러 시 기본값
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
    배당률(%)과 성장률(%)을 아주 보수적으로 계산하는 함수
    """
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info
        
        # --- [1] 현재 배당률(Yield) 구하기 ---
        # 전략: 배당률(%)보다는 '주당 배당금(Rate)'이 훨씬 정확하므로 그걸 먼저 찾음
        
        div_rate = info.get('dividendRate') # 예: 삼성전자 1444원
        current_price = info.get('currentPrice')
        
        # 가격 정보가 info에 없으면 history에서 가져옴
        if not current_price:
            h = t.history(period="1d")
            if not h.empty:
                current_price = h['Close'].iloc[-1]
        
        yield_pct = 0.0
        
        # Case A: '주당 배당금' 데이터가 확실히 있을 때 (가장 정확)
        if div_rate and current_price and current_price > 0:
            yield_pct = (div_rate / current_price) * 100
            
        # Case B: 주당 배당금은 없는데, 'Trailing Annual Rate'(작년 기준)는 있을 때 (ETF용)
        elif info.get('trailingAnnualDividendRate') and current_price and current_price > 0:
             # ETF는 이게 더 정확함
            yield_pct = (info.get('trailingAnnualDividendRate') / current_price) * 100
            
        # Case C: 다 없고 그냥 'dividendYield' 퍼센트만 있을 때
        elif info.get('dividendYield'):
            yield_pct = info.get('dividendYield') * 100

        # --- [2] 배당 성장률 (CAGR) 구하기 ---
        growth_rate = 0.0
        try:
            divs = t.dividends
            if len(divs) > 0:
                # 연도별 합계 (올해 데이터가 불완전하면 제외하기 위해 로직 강화)
                annual = divs.resample('Y').sum()
                
                # 데이터가 충분하면 (최소 4년)
                if len(annual) >= 4:
                    # '작년' 확정 배당금 vs '5년 전' 확정 배당금 비교
                    # (올해는 아직 진행중이라 제외하는 게 안전함)
                    last_full_year = annual.iloc[-2] # 작년
                    past_year = annual.iloc[-6] if len(annual) >= 6 else annual.iloc[0]
                    
                    if past_year > 0 and last_full_year > 0:
                        years = len(annual) - 2 if len(annual) < 6 else 4
                        growth_rate = ((last_full_year / past_year) ** (1/years) - 1) * 100
        except Exception:
            growth_rate = 0.0
            
        return yield_pct, growth_rate

    except Exception as e:
        # 에러나면 그냥 0, 0 반환 (터지는 것 방지)
        return 0.0, 0.0
