import time
from binance.exceptions import BinanceAPIException
from bot.logging_config import setup_logger

logger = setup_logger()

def place_twap_order(client, symbol, side, total_qty, num_slices, interval_seconds):
    """
    TWAP - Time Weighted Average Price
    Split a big order into equal chunks over equal time intervals
    """
    # Get symbol info for precision
    exchange_info = client.futures_exchange_info()
    symbol_info = None
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            symbol_info = s
            break
    
    if not symbol_info:
        raise ValueError(f"Symbol {symbol} not found")
    
    # Find quantity precision
    qty_precision = 6  # default
    for f in symbol_info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step_size = f['stepSize']
            qty_precision = len(step_size.split('.')[1].rstrip('0')) if '.' in step_size else 0
            break
    
    slice_qty = round(total_qty / num_slices, qty_precision)
    results = []

    logger.info(f"Starting TWAP: {total_qty} {symbol} in {num_slices} slices over {interval_seconds}s intervals")
    logger.info(f"Slice quantity: {slice_qty} (precision: {qty_precision})")

    for i in range(num_slices):
        try:
            logger.info(f"Placing TWAP slice {i+1}/{num_slices}: {slice_qty} {symbol}")
            
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=slice_qty
            )
            results.append(order)
            logger.info(f"TWAP slice {i+1} placed: Order ID {order['orderId']}")

            if i < num_slices - 1:  # Don't sleep after the last slice
                logger.info(f"Waiting {interval_seconds}s before next slice...")
                time.sleep(interval_seconds)

        except BinanceAPIException as e:
            logger.error(f"TWAP slice {i+1} failed: {e.message}")
            raise

    logger.info(f"TWAP completed: {len(results)} slices executed")
    return results

def place_stop_limit_order(client, symbol, side, quantity, stop_price, limit_price):
    """
    Stop-Limit Order
    Triggers when stop price is hit, but executes at limit price or better
    """
    logger.info(f"Placing Stop-Limit: {quantity} {symbol} - Stop: {stop_price}, Limit: {limit_price}")
    
    try:
        # Determine order type based on side
        if side.upper() == "BUY":
            order_type = "TAKE_PROFIT"  # Buy stop order
        else:
            order_type = "STOP"  # Sell stop order
            
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            stopPrice=stop_price,  # triggers the order
            price=limit_price,     # actual limit price
            timeInForce="GTC"
        )
        logger.info(f"Stop-Limit placed: Order ID {order['orderId']}")
        return order
    except BinanceAPIException as e:
        logger.error(f"Stop-Limit failed: {e.message}")
        raise

def place_iceberg_order(client, symbol, side, total_qty, visible_qty, price):
    """
    Iceberg Order
    Shows only small visible chunks, hides the total order size
    """
    filled = 0
    orders = []

    logger.info(f"Starting Iceberg: {total_qty} {symbol} in chunks of {visible_qty}")

    while filled < total_qty:
        try:
            # Only show `visible_qty` at a time
            remaining = total_qty - filled
            chunk = min(visible_qty, remaining)

            logger.info(f"Placing Iceberg chunk: {chunk} {symbol} (filled: {filled}/{total_qty})")

            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=chunk,
                price=price,
                timeInForce="GTC"
            )
            orders.append(order)

            # Wait until this chunk fills before placing next
            logger.info(f"Waiting for chunk {len(orders)} to fill...")
            while True:
                status = client.futures_get_order(
                    symbol=symbol,
                    orderId=order['orderId']
                )
                
                if status['status'] == 'FILLED':
                    filled += chunk
                    logger.info(f"Chunk filled! Total filled: {filled}/{total_qty}")
                    break
                elif status['status'] in ['CANCELED', 'EXPIRED', 'REJECTED']:
                    logger.error(f"Chunk {order['orderId']} {status['status']}. Stopping iceberg.")
                    raise Exception(f"Iceberg chunk {status['status']}")
                
                time.sleep(2)  # Check every 2 seconds

        except BinanceAPIException as e:
            logger.error(f"Iceberg chunk failed: {e.message}")
            raise

    logger.info(f"Iceberg completed: {len(orders)} chunks filled")
    return orders

def setup_grid_orders(client, symbol, current_price, num_levels, spacing_pct, qty_per_level):
    """
    Grid Trading
    Places a grid of buy and sell orders at fixed intervals
    """
    orders = []
    
    # Get symbol info for price precision
    exchange_info = client.futures_exchange_info()
    symbol_info = None
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            symbol_info = s
            break
    
    if not symbol_info:
        raise ValueError(f"Symbol {symbol} not found")
    
    # Find price precision and tick size
    price_precision = 2  # default
    tick_size = 0.01  # default
    for f in symbol_info['filters']:
        if f['filterType'] == 'PRICE_FILTER':
            tick_size = float(f['tickSize'])
            price_precision = len(str(tick_size).split('.')[1].rstrip('0')) if '.' in str(tick_size) else 0
            break
    
    logger.info(f"Setting up Grid: {num_levels} levels, {spacing_pct}% spacing, {qty_per_level} per level")
    logger.info(f"Current price: ${current_price}, Tick size: {tick_size}, Precision: {price_precision}")

    for i in range(1, num_levels + 1):
        try:
            # Place buy orders BELOW current price
            buy_price = round(current_price * (1 - spacing_pct * i / 100), price_precision)
            # Ensure buy price respects tick size
            buy_price = round(buy_price / tick_size) * tick_size
            
            buy_order = client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="LIMIT",
                quantity=qty_per_level,
                price=buy_price,
                timeInForce="GTC"
            )
            orders.append(("BUY", buy_price, buy_order))
            logger.info(f"Grid BUY order placed: {qty_per_level} @ {buy_price}")

            # Place sell orders ABOVE current price
            sell_price = round(current_price * (1 + spacing_pct * i / 100), price_precision)
            # Ensure sell price respects tick size
            sell_price = round(sell_price / tick_size) * tick_size
            
            sell_order = client.futures_create_order(
                symbol=symbol,
                side="SELL",
                type="LIMIT",
                quantity=qty_per_level,
                price=sell_price,
                timeInForce="GTC"
            )
            orders.append(("SELL", sell_price, sell_order))
            logger.info(f"Grid SELL order placed: {qty_per_level} @ {sell_price}")

        except BinanceAPIException as e:
            logger.error(f"Grid order level {i} failed: {e.message}")
            raise

    logger.info(f"Grid setup completed: {len(orders)} orders placed")
    return orders

def get_current_price(client, symbol):
    """Get current market price for grid setup"""
    try:
        ticker = client.futures_ticker(symbol=symbol)
        return float(ticker['lastPrice'])
    except BinanceAPIException as e:
        logger.error(f"Failed to get current price: {e.message}")
        raise
