import logging
import os

def setup_logger():
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # File handler — saves logs to file
    file_handler = logging.FileHandler("logs/bot.log")
    file_handler.setLevel(logging.DEBUG)

    # Console handler — prints to terminal too
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
