import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    POLY_SOURCE_URL = os.getenv("POLY_SOURCE_URL")
    POLY_SOURCE_TYPE = os.getenv("POLY_SOURCE_TYPE", "rest")

    # Comma-separated keywords to filter markets (e.g., "election,president,war")
    POLY_MARKET_KEYWORDS = os.getenv("POLY_MARKET_KEYWORDS", "")
    # Optional: custom GraphQL query to fetch trades (overrides built-in attempts)
    POLY_GRAPHQL_TRADES_QUERY = os.getenv("POLY_GRAPHQL_TRADES_QUERY", "")
    # Primary public subgraph URL (The Graph / Goldsky) - optional but recommended for public access
    POLY_SUBGRAPH_URL = os.getenv("POLY_SUBGRAPH_URL", "https://api.thegraph.com/subgraphs/name/Polymarket/polymarket-subgraph")
    # Optional: authentication for Gamma API
    # POLY_AUTH_HEADER accepts a header string, e.g. "Authorization: Bearer <token>" or just the token
    POLY_AUTH_HEADER = os.getenv("POLY_AUTH_HEADER", "")
    # POLY_AUTH_COOKIE accepts a cookie string, e.g. "__cf_bm=...; session=..."
    POLY_AUTH_COOKIE = os.getenv("POLY_AUTH_COOKIE", "")

    ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
    ETHERSCAN_API_URL = os.getenv("ETHERSCAN_API_URL", "https://api.etherscan.io/api")

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT")

    ALERT_USDC_THRESHOLD = float(os.getenv("ALERT_USDC_THRESHOLD", 5000))
    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", 30))

    SQLITE_PATH = os.getenv("SQLITE_PATH", "./polymonitor.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
