from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)
API_KEY = "API KEY"

def get_stock_price(symbol):
    try:
        data = requests.get(
            "https://",
            params={
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": "1min",
                "apikey": API_KEY
            }
        ).json()
        
        latest = data["Time Series (1min)"][sorted(data["Time Series (1min)"])[-1]]
        return round(float(latest["4. close"]), 2)
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_price', methods=['POST'])
def get_price():
    symbol = request.get_json().get("symbol", "").upper()
    if not symbol:
        return jsonify({"error": "Stock symbol required"}), 400
    
    price = get_stock_price(symbol)
    return jsonify({"symbol": symbol, "price": price}) if price else (
        jsonify({"error": "Invalid stock symbol or no data available"}), 400
    )

if __name__ == '__main__':
    app.run(debug=True)