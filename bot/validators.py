VALID_SIDES = ["BUY", "SELL"]
VALID_TYPES = ["MARKET", "LIMIT", "TWAP", "STOP_LIMIT", "ICEBERG", "GRID"]

def validate_inputs(symbol, side, order_type, quantity, price=None):
    errors = []

    if not symbol or len(symbol) < 3:
        errors.append("Invalid symbol. Example: BTCUSDT")

    # Side validation (not required for GRID)
    if order_type.upper() != "GRID":
        if not side:
            errors.append("Side is required for this order type")
        elif side.upper() not in VALID_SIDES:
            errors.append(f"Side must be one of: {VALID_SIDES}")

    if order_type.upper() not in VALID_TYPES:
        errors.append(f"Order type must be one of: {VALID_TYPES}")

    # Quantity validation for order types that need it
    if order_type.upper() not in ["GRID"]:
        if quantity is None:
            errors.append("Quantity is required for this order type")
        elif quantity <= 0:
            errors.append("Quantity must be greater than 0")

    # Price validation for order types that need it
    if order_type.upper() == "LIMIT":
        if price is None:
            errors.append("Price is required for LIMIT orders")
        elif price <= 0:
            errors.append("Price must be greater than 0")

    if errors:
        raise ValueError("\n".join(errors))

def validate_algorithm_inputs(args):
    """Validate algorithm-specific parameters"""
    errors = []
    order_type = args.type.upper()

    if order_type == "TWAP":
        if not args.slices or args.slices <= 0:
            errors.append("TWAP requires --slices (number of slices > 0)")
        if not args.interval or args.interval <= 0:
            errors.append("TWAP requires --interval (seconds between slices > 0)")

    elif order_type == "STOP_LIMIT":
        if not args.stop or args.stop <= 0:
            errors.append("STOP_LIMIT requires --stop (stop price > 0)")
        if not args.price or args.price <= 0:
            errors.append("STOP_LIMIT requires --price (limit price > 0)")

    elif order_type == "ICEBERG":
        if not args.visible or args.visible <= 0:
            errors.append("ICEBERG requires --visible (visible quantity > 0)")
        if not args.price or args.price <= 0:
            errors.append("ICEBERG requires --price (limit price > 0)")
        if args.visible >= args.quantity:
            errors.append("ICEBERG visible quantity must be less than total quantity")

    elif order_type == "GRID":
        if not args.levels or args.levels <= 0:
            errors.append("GRID requires --levels (number of levels > 0)")
        if not args.spacing or args.spacing <= 0:
            errors.append("GRID requires --spacing (percentage spacing > 0)")
        if not args.quantity or args.quantity <= 0:
            errors.append("GRID requires --quantity (quantity per level > 0)")

    if errors:
        raise ValueError("\n".join(errors))
