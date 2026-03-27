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
        # Configure client for testnet with explicit URLs
        client = Client(
            api_key=api_key,
            api_secret=api_secret,
            tld='com',  # Use .com domain
            testnet=True
        )
        
        # Test the connection
        logger.info("Testing Binance Testnet connection...")
        server_time = client.get_server_time()
        logger.info(f"Connected successfully. Server time: {server_time}")
        
        return client
    except BinanceAPIException as e:
        logger.error(f"Binance API error: {e.message} (code: {e.code})")
        if e.code == -2015:
            logger.error("This appears to be a geographical restriction. Try using a VPN or check Binance's terms of service.")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to Binance: {e}")
        raise
