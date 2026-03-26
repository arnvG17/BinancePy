import argparse
import sys
from bot.client import get_client
from bot.validators import validate_inputs, validate_algorithm_inputs
from bot.orders import place_order, print_order_summary
from bot.algorithms import (
    place_twap_order, place_stop_limit_order, 
    place_iceberg_order, setup_grid_orders, get_current_price
)
from bot.logging_config import setup_logger

logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description="Binance Futures Testnet Trading Bot")

    parser.add_argument("--symbol",   required=True,  help="e.g. BTCUSDT")
    parser.add_argument("--side",     required=False, help="BUY or SELL (not required for GRID)")
    parser.add_argument("--type",     required=True,  help="MARKET, LIMIT, TWAP, STOP_LIMIT, ICEBERG, GRID")
    parser.add_argument("--quantity", required=False, type=float, help="e.g. 0.01")
    parser.add_argument("--price",    required=False, type=float, help="Required for LIMIT orders")
    
    # Algorithm-specific parameters
    parser.add_argument("--slices",    required=False, type=int, help="Number of slices for TWAP")
    parser.add_argument("--interval",  required=False, type=int, help="Interval between TWAP slices (seconds)")
    parser.add_argument("--stop",      required=False, type=float, help="Stop price for STOP_LIMIT orders")
    parser.add_argument("--visible",   required=False, type=float, help="Visible quantity for ICEBERG orders")
    parser.add_argument("--levels",    required=False, type=int, help="Number of levels for GRID orders")
    parser.add_argument("--spacing",   required=False, type=float, help="Spacing percentage for GRID orders")

    args = parser.parse_args()

    # Validate inputs
    try:
        validate_inputs(args.symbol, args.side, args.type, args.quantity, args.price)
        validate_algorithm_inputs(args)
    except ValueError as e:
        print(f"\n❌ Validation Error:\n{e}\n")
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    # Connect to Binance
    try:
        client = get_client()
    except Exception as e:
        print(f"\n❌ Connection Error: {e}\n")
        sys.exit(1)

    # Place the order based on type
    try:
        order_type = args.type.upper()
        
        if order_type == "MARKET" or order_type == "LIMIT":
            # Simple market or limit orders
            params = {
                "symbol": args.symbol,
                "side": args.side,
                "type": args.type,
                "quantity": args.quantity,
            }
            if args.price:
                params["price"] = args.price

            response = place_order(client, args.symbol, args.side, args.type, args.quantity, args.price)
            print_order_summary(params, response)
            
        elif order_type == "TWAP":
            # TWAP algorithm
            response = place_twap_order(client, args.symbol, args.side, args.quantity, args.slices, args.interval)
            print(f"\n✅ TWAP Order Completed: {len(response)} slices executed")
            
        elif order_type == "STOP_LIMIT":
            # Stop-Limit order
            response = place_stop_limit_order(client, args.symbol, args.side, args.quantity, args.stop, args.price)
            print(f"\n✅ Stop-Limit Order Placed: ID {response['orderId']}")
            print(f"   Stop Price: ${args.stop}")
            print(f"   Limit Price: ${args.price}")
            
        elif order_type == "ICEBERG":
            # Iceberg order
            response = place_iceberg_order(client, args.symbol, args.side, args.quantity, args.visible, args.price)
            print(f"\n✅ Iceberg Order Completed: {len(response)} chunks filled")
            
        elif order_type == "GRID":
            # Grid trading
            current_price = get_current_price(client, args.symbol)
            response = setup_grid_orders(client, args.symbol, current_price, args.levels, args.spacing, args.quantity)
            print(f"\n✅ Grid Setup Completed: {len(response)} orders placed")
            print(f"   Current Price: ${current_price}")
            print(f"   Grid Levels: {args.levels} above and below current price")
            
        else:
            print(f"\n❌ Unknown order type: {order_type}")
            sys.exit(1)

        print("✅ Order executed successfully!")

    except Exception as e:
        print(f"\n❌ Order Failed: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
