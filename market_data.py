import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600) # 1시간마다 갱신 (배당은 자주 안 바뀌니까)
def get_usd_krw_rate():
    try:
        # 야후 파이낸스에서 원/달러 환율 가져오기
        ticker = yf.Ticker("KRW=X")
        history = ticker.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
        return 1400.0 # 실패 시 기본값
    except:
        return 1400.0

@st.cache_data(ttl=600) # 10분 캐시
def fetch_current_price(ticker_symbol):
    """
    현재 가격과 통화 정보만 가져오는 함수
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. 빠른 가격 조회 (history 사용)
        history = ticker.history(period="1d")
        if history.empty:
            return None, "KRW", ticker_symbol
            
        current_price = history['Close'].iloc[-1]
        
        # 2. 메타 데이터 (이름, 통화)
        info = ticker.info
        currency = info.get('currency', 'KRW')
        short_name = info.get('shortName', ticker_symbol)
        
        # 한국 주식은 이름이 깨질 때가 많아서 티커로 대체할 수도 있음
        if ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ"):
            currency = "KRW"
            
        return current_price, currency, short_name
    except Exception as e:
        return None, "KRW", ticker_symbol

@st.cache_data(ttl=86400) # 24시간 캐시 (배당 정보는 하루 1번이면 충분)
def fetch_dividend_info(ticker_symbol):
    """
    배당률(%)과 5년 배당 성장률(%)을 자동으로 계산하는 함수
    """
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info
        
        # 1. 현재 예상 배당률 (Forward Dividend Yield)
        # 데이터가 없으면 0.0으로 처리
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield is None:
            dividend_yield = 0
        
        yield_pct = dividend_yield * 100 # 0.05 -> 5.0% 변환
        
        # 2. 배당 성장률 계산 (Dividend Growth Rate - 5 Year CAGR)
        growth_rate = 0.0
        try:
            # 배당금 내역 전체 가져오기
            divs = t.dividends
            
            if len(divs) > 0:
                # 연도별로 합계 계산 (Resample)
                annual_divs = divs.resample('Y').sum()
                
                # 최소 4년치 데이터가 있어야 성장률 계산 가능
                if len(annual_divs) >= 4:
                    # 최근 배당금 (작년 or 올해 예상)
                    latest_div = annual_divs.iloc[-1]
                    # 5년 전 배당금
                    past_div = annual_divs.iloc[-5] if len(annual_divs) >= 5 else annual_divs.iloc[0]
                    
                    if past_div > 0:
                        # 연평균 성장률(CAGR) 공식
                        years = len(annual_divs) if len(annual_divs) < 5 else 5
                        growth_rate = ((latest_div / past_div) ** (1/years) - 1) * 100
        except:
            growth_rate = 0.0 # 계산 실패 시 0
            
        return yield_pct, growth_rate

    except:
        return 0.0, 0.0
