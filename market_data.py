import yfinance as yf
import pandas as pd

def get_usd_krw_rate():
    try:
        ticker = yf.Ticker("KRW=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return 1300.0
    except:
        return 1300.0

def fetch_current_price(ticker):
    try:
        asset = yf.Ticker(ticker)
        hist = asset.history(period="1d")
        if hist.empty:
            return None, None, None
        
        current_price = hist['Close'].iloc[-1]
        info = asset.info
        name = info.get('longName') or info.get('shortName') or ticker
        
        if ticker.endswith('.KS') or ticker.endswith('.KQ'):
            currency = 'KRW'
        else:
            currency = 'USD'

        return current_price, currency, name
    except:
        return None, None, None
