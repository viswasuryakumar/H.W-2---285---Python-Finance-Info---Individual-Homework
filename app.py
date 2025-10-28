from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.get_info()
        
        # Get current price and previous close
        current_price = stock.fast_info['lastPrice'] if hasattr(stock.fast_info, 'lastPrice') else stock.history(period='1d')['Close'][-1]
        prev_close = stock.fast_info['previousClose'] if hasattr(stock.fast_info, 'previousClose') else stock.history(period='2d')['Close'][-2]
        
        # Calculate changes
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            'name': info.get('longName', symbol),
            'symbol': symbol.upper(),
            'current_price': f"${current_price:.2f}",
            'change': f"{'+' if change > 0 else ''}{change:.2f}",
            'change_percent': f"{'+' if change_percent > 0 else ''}{change_percent:.2f}%",
            'timestamp': datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        }
    except Exception as e:
        return None

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
    app.run(debug=True)