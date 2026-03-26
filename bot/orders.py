from binance.exceptions import BinanceAPIException
from bot.logging_config import setup_logger

logger = setup_logger()

def place_order(client, symbol, side, order_type, quantity, price=None):
    params = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": quantity,
    }

    if order_type.upper() == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"   # Good Till Cancelled

    logger.info(f"Placing order with params: {params}")

    try:
        response = client.futures_create_order(**params)
        logger.info(f"Order response: {response}")
        return response
    except BinanceAPIException as e:
        logger.error(f"Binance API error: {e.message} (code: {e.code})")
        raise
    except Exception as e:
        logger.error(f"Unexpected error placing order: {e}")
        raise

def print_order_summary(params, response):
    print("\n========== ORDER SUMMARY ==========")
    print(f"  Symbol   : {params['symbol']}")
    print(f"  Side     : {params['side']}")
    print(f"  Type     : {params['type']}")
    print(f"  Quantity : {params['quantity']}")
    if 'price' in params:
        print(f"  Price    : {params['price']}")

    print("\n========== ORDER RESPONSE ==========")
    print(f"  Order ID     : {response.get('orderId')}")
    print(f"  Status       : {response.get('status')}")
    print(f"  Executed Qty : {response.get('executedQty')}")
    print(f"  Avg Price    : {response.get('avgPrice', 'N/A')}")
    print("====================================\n")
