import asyncio
import time
from datetime import datetime
from .adapter import get_adapter
from .store import Store
from .config import settings
from .blockchain import is_wallet_new
from .alerts import send_alert_email

class Monitor:
    def __init__(self):
        self.adapter = get_adapter()
        self.store = Store(settings.SQLITE_PATH)
        self.poll_interval = settings.POLL_INTERVAL_SECONDS
        self.threshold = settings.ALERT_USDC_THRESHOLD

    async def process_trade(self, trade):
        # trade dict must contain: tx_hash, wallet, market_id, market_name, amount_usdc, timestamp
        tx = trade.get('tx_hash') or trade.get('txHash')
        wallet = trade.get('wallet')
        market_id = trade.get('market_id') or trade.get('market', {}).get('id')
        market_name = trade.get('market_name') or trade.get('market', {}).get('title')
        amount = float(trade.get('amount_usdc') or trade.get('amount') or 0)
        ts = int(trade.get('timestamp') or int(time.time()))

        # Add trade to store
        await self.store.add_trade(tx, wallet, market_id, market_name, amount, ts)

        # Signal 2: large single trade
        if amount >= self.threshold:
            send_alert_email(wallet, amount, market_name, f'单笔金额≥{self.threshold} USDC')

        # Signal 1: new wallet (first chain tx <24h) and no prior Polymarket trades
        has_prior = await self.store.wallet_has_prior_polymarket_trades(wallet)
        if not has_prior:
            is_new = is_wallet_new(wallet)
            if is_new:
                send_alert_email(wallet, amount, market_name, '新钱包（链上首次交易<24h）')

        # Signal 3: high-frequency same wallet same market >=3 in 24h
        cnt = await self.store.count_wallet_market_recent(wallet, market_id)
        if cnt >= 3:
            send_alert_email(wallet, amount, market_name, f'24小时在同一市场交易≥3次（{cnt}次）')

    async def run_once(self):
        trades = await self.adapter.fetch_recent_trades()
        # Expect trades as list of dicts; deduplicate by tx_hash
        seen = set()
        for t in trades:
            tx = t.get('tx_hash') or t.get('txHash')
            if not tx or tx in seen:
                continue
            seen.add(tx)
            await self.process_trade(t)

    async def run(self):
        await self.store.init()
        while True:
            try:
                await self.run_once()
            except Exception as e:
                print('Error in monitor loop', e)
            await asyncio.sleep(self.poll_interval)
