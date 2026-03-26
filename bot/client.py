import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
from bot.logging_config import setup_logger

load_dotenv()
logger = setup_logger()

def get_client():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_SECRET")

    if not api_key or not api_secret:
        logger.error("API keys missing. Check your .env file.")
        raise ValueError("Missing API keys in .env file")

    try:
        client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True          # This points to testnet automatically
        )
        logger.info("Binance Testnet client initialized successfully.")
        return client
    except BinanceAPIException as e:
        logger.error(f"Failed to connect to Binance: {e}")
        raise
