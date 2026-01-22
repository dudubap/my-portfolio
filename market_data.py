import yfinance as yf
import pandas as pd

def get_usd_krw_rate():
    """환율 가져오기 (안전 모드)"""
    try:
        # 1. 1분 데이터 시도
        ticker = yf.Ticker("KRW=X")
        data = ticker.history(period="1d", interval="1m")
        
        # 2. 실패하면 그냥 오늘 하루치 데이터 시도
        if data.empty:
            data = ticker.history(period="1d")
            
        if not data.empty:
            return data['Close'].iloc[-1]
        return 1300.0 # 정 안되면 기본값
    except:
        return 1300.0

def fetch_current_price(ticker):
    """현재가 가져오기 (3중 안전장치)"""
    try:
        # 티커 앞뒤 공백 제거 (실수 방지)
        ticker = ticker.strip().upper()
        asset = yf.Ticker(ticker)
        
        # 시도 1: 가장 최신 1분 데이터 (장중일 때 최고)
        hist = asset.history(period="1d", interval="1m")
        
        # 시도 2: 1분이 안 되면 오늘 하루치 (장 마감 후 or 차단 시)
        if hist.empty:
            hist = asset.history(period="1d")
            
        # 시도 3: 그것도 안 되면 최근 5일치 (주말/휴일 대비)
        if hist.empty:
            hist = asset.history(period="5d")
        
        if hist.empty:
            print(f"데이터 없음: {ticker}")
            return None, None, None
        
        # 가장 마지막 줄(최신) 가격 선택
        current_price = hist['Close'].iloc[-1]
        
        # 종목 정보 가져오기 (에러가 나도 가격은 건지도록 분리)
        try:
            info = asset.info
            name = info.get('longName') or info.get('shortName') or ticker
        except:
            name = ticker # 이름 못 가져오면 티커로 대체
        
        # 통화 설정
        if ticker.endswith('.KS') or ticker.endswith('.KQ'):
            currency = 'KRW'
        else:
            currency = 'USD'

        return current_price, currency, name

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None, None, None
