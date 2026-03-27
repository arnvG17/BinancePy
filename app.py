from flask import Flask, request, render_template_string, jsonify
import os
from bot.client import get_client
from bot.orders import place_order
from bot.validators import validate_inputs

app = Flask(__name__)

def get_trading_pairs():
    """Get available trading pairs from Binance futures"""
    try:
        client = get_client()
        exchange_info = client.futures_exchange_info()
        symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
        # Filter for USDT pairs and sort them
        usdt_pairs = sorted([s for s in symbols if s.endswith('USDT')])
        return usdt_pairs
    except Exception as e:
        print(f"Error fetching trading pairs from Binance: {e}")
        print("Using fallback trading pairs...")
        # Return common pairs as fallback
        return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT']

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Binance Trading Bot</title>
    <style>
        @import url('https: //fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #ffffff;
            color: #000000;
            min-height: 100vh;
            padding: 40px;
        }
        
        .container {
            max-width: 480px;
            margin: 0 auto;
            border: 1px solid #000000;
        }
        
        .header {
            border-bottom: 1px solid #000000;
            padding: 24px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 4px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .header p {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .form-container {
            padding: 32px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: #000000;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        input, select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #000000;
            border-radius: 0;
            font-size: 14px;
            background: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }
        
        input:focus, select:focus {
            outline: none;
            border-width: 2px;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        
        .submit-btn {
            width: 100%;
            padding: 12px;
            background: #000000;
            color: #ffffff;
            border: 1px solid #000000;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'JetBrains Mono', monospace;
            transition: all 0.2s ease;
            margin-top: 8px;
        }
        
        .submit-btn:hover {
            background: #ffffff;
            color: #000000;
        }
        
        .result-container {
            margin-top: 32px;
            padding: 20px;
            border: 1px solid #000000;
        }
        
        .result-container h3 {
            margin-bottom: 12px;
            color: #000000;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }
        
        .result-content {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            line-height: 1.6;
            color: #000000;
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        .success {
            background: #ffffff;
        }
        
        .success h3 {
            color: #000000;
        }
        
        .error {
            background: #ffffff;
        }
        
        .error h3 {
            color: #000000;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 2px solid #ffffff;
            border-top: 2px solid #000000;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .price-input {
            display: none;
        }
        
        .price-input.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Binance Trading Bot UI</h1>
            <p>Binance Testnet Trading Interface</p>
        </div>
        
        <div class="form-container">
            <form method="post" id="orderForm">
                <div class="form-group">
                    <label for="symbol">Trading Pair</label>
                    <select id="symbol" name="symbol" required>
                        <option value="">Select a trading pair</option>
                        {% for pair in trading_pairs %}
                        <option value="{{ pair }}">{{ pair }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="side">Order Side</label>
                        <select id="side" name="side" required>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="type">Order Type</label>
                        <select id="type" name="type" required onchange="togglePriceField()">
                            <option value="MARKET">MARKET</option>
                            <option value="LIMIT">LIMIT</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="quantity">Quantity</label>
                    <input type="number" id="quantity" name="quantity" step="0.00001" min="0.00001" placeholder="0.001" required>
                </div>
                
                <div class="form-group price-input" id="priceGroup">
                    <label for="price">Price</label>
                    <input type="number" id="price" name="price" step="0.01" min="0.01" placeholder="50000.00">
                </div>
                
                <button type="submit" class="submit-btn">Place Order</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Processing order...</p>
            </div>
            
            {% if result %}
            <div class="result-container {{ 'success' if result.success else 'error' }}">
                <h3>{{ 'Order Placed' if result.success else 'Error' }}</h3>
                <div class="result-content">{{ result.content }}</div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        function togglePriceField() {
            const orderType = document.getElementById('type').value;
            const priceGroup = document.getElementById('priceGroup');
            const priceInput = document.getElementById('price');
            
            if (orderType === 'LIMIT') {
                priceGroup.classList.add('show');
                priceInput.required = true;
            } else {
                priceGroup.classList.remove('show');
                priceInput.required = false;
                priceInput.value = '';
            }
        }
        
        document.getElementById('orderForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
        });
        
        document.getElementById('symbol').focus();
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    trading_pairs = get_trading_pairs()

    if request.method == "POST":
        try:
            symbol = request.form["symbol"]
            side = request.form["side"]
            order_type = request.form["type"]
            quantity = float(request.form["quantity"])
            price = request.form.get("price")

            price = float(price) if price else None

            # Use the correct validation function name
            validate_inputs(symbol, side, order_type, quantity, price)

            client = get_client()
            order = place_order(client, symbol, side, order_type, quantity, price)

            result_data = {
                "orderId": order.get("orderId"),
                "status": order.get("status"),
                "executedQty": order.get("executedQty"),
                "avgPrice": order.get("avgPrice"),
                "symbol": order.get("symbol"),
                "side": order.get("side"),
                "type": order.get("type"),
                "origQty": order.get("origQty")
            }
            
            result = {
                "success": True,
                "content": f"Order ID: {result_data['orderId']}\n"
                          f"Status: {result_data['status']}\n"
                          f"Symbol: {result_data['symbol']}\n"
                          f"Side: {result_data['side']}\n"
                          f"Type: {result_data['type']}\n"
                          f"Quantity: {result_data['origQty']}\n"
                          f"Executed: {result_data['executedQty']}\n"
                          f"Avg Price: {result_data.get('avgPrice', 'N/A')}"
            }

        except Exception as e:
            result = {
                "success": False,
                "content": str(e)
            }

    return render_template_string(HTML, result=result, trading_pairs=trading_pairs)

@app.route("/api/account")
def account_info():
    try:
        client = get_client()
        account = client.futures_account()
        balances = [b for b in account['assets'] if float(b['walletBalance']) > 0]
        return jsonify({
            "success": True,
            "balances": balances,
            "totalWalletBalance": account['totalWalletBalance']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
