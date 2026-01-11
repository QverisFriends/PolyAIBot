import aiosqlite
import asyncio
from datetime import datetime, timedelta

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash TEXT,
    wallet TEXT,
    market_id TEXT,
    market_name TEXT,
    amount_usdc REAL,
    timestamp INTEGER
);
"""

class Store:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_lock = asyncio.Lock()
        self.initialized = False

    async def init(self):
        async with self._init_lock:
            if self.initialized:
                return
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(SCHEMA)
                await db.commit()
            self.initialized = True

    async def add_trade(self, tx_hash, wallet, market_id, market_name, amount_usdc, timestamp):
        await self.init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO trades (tx_hash,wallet,market_id,market_name,amount_usdc,timestamp) VALUES (?,?,?,?,?,?)",
                (tx_hash, wallet, market_id, market_name, amount_usdc, int(timestamp))
            )
            await db.commit()

    async def count_wallet_market_recent(self, wallet, market_id, within_seconds=24*3600):
        await self.init()
        cutoff = int((datetime.utcnow() - timedelta(seconds=within_seconds)).timestamp())
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM trades WHERE wallet=? AND market_id=? AND timestamp>=?",
                (wallet, market_id, cutoff)
            )
            row = await cursor.fetchone()
            return row[0]

    async def wallet_has_prior_polymarket_trades(self, wallet):
        await self.init()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM trades WHERE wallet=?",
                (wallet,)
            )
            row = await cursor.fetchone()
            return row[0] > 0
