from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime
import os
import logging


import os
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# Ensure logs are printed to stdout (helpful on Render)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)

        # Safely fetch info and fast_info (they can raise or be empty)
        try:
            info = stock.get_info() or {}
        except Exception:
            info = {}

        try:
            fi = getattr(stock, "fast_info") or {}
        except Exception:
            fi = {}

        # Try several places for current price and previous close
        current_price = None
        prev_close = None

        if isinstance(fi, dict):
            current_price = fi.get("lastPrice") or fi.get("regularMarketPrice")
            prev_close = fi.get("previousClose") or fi.get("previous_close")

        # Fallback to history if fast_info didn't provide values
        if current_price is None:
            hist = stock.history(period="1d")
            if hist is not None and not hist.empty:
                current_price = float(hist["Close"].dropna().iloc[-1])

        if prev_close is None:
            hist2 = stock.history(period="2d")
            if hist2 is not None and not hist2.empty and len(hist2["Close"].dropna()) >= 2:
                prev_close = float(hist2["Close"].dropna().iloc[-2])

        # If still missing, set prev_close = current_price so change is zero instead of crashing
        if current_price is None:
            raise ValueError(f"No price data returned for symbol: {symbol}")

        if prev_close is None:
            prev_close = current_price

        change = current_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close not in (0, None) else 0.0

        return {
            "name": info.get("longName") or info.get("shortName") or symbol.upper(),
            "symbol": symbol.upper(),
            "current_price": f"${current_price:.2f}",
            "change": f"{('+' if change > 0 else '')}{change:.2f}",
            "change_percent": f"{('+' if change_percent > 0 else '')}{change_percent:.2f}%",
            "timestamp": datetime.now().strftime("%a %b %d %H:%M:%S %Y"),
        }
    except Exception as e:
        # Log the exception so Render logs contain the traceback
        app.logger.exception("Error fetching stock %s", symbol)
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/quote', methods=['POST'])
def get_quote():
    symbol = request.form.get('symbol', '').strip()
    if not symbol:
        return jsonify({'error': 'Please enter a stock symbol'})
    
    stock_info = get_stock_info(symbol)
    if stock_info is None:
        return jsonify({'error': f'Unable to fetch data for symbol: {symbol}'})
    
    return jsonify(stock_info)

if __name__ == '__main__':
    # Development only
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))