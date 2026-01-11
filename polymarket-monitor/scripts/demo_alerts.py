import asyncio
from src.polymarket_monitor.monitor import Monitor
from src.polymarket_monitor import blockchain

async def main():
    m = Monitor()
    await m.store.init()

    print('\n-- Simulate single large trade (>=threshold) --')
    trade_large = {'tx_hash':'0xdemo1','wallet':'0xAAA','market_id':'0xM1','market_name':'Test Market','amount_usdc':m.threshold+100,'timestamp':1620000000}
    await m.process_trade(trade_large)

    print('\n-- Simulate high-frequency trades (3 in 24h) --')
    trade_h1 = {'tx_hash':'0xhf1','wallet':'0xHF','market_id':'0xM2','market_name':'HF Market','amount_usdc':10,'timestamp':1620000100}
    trade_h2 = {'tx_hash':'0xhf2','wallet':'0xHF','market_id':'0xM2','market_name':'HF Market','amount_usdc':20,'timestamp':1620000200}
    trade_h3 = {'tx_hash':'0xhf3','wallet':'0xHF','market_id':'0xM2','market_name':'HF Market','amount_usdc':30,'timestamp':1620000300}
    await m.process_trade(trade_h1)
    await m.process_trade(trade_h2)
    await m.process_trade(trade_h3)

    print('\n-- Simulate new wallet alert (monkeypatch is_wallet_new -> True) --')
    blockchain.is_wallet_new = lambda w: True
    trade_new = {'tx_hash':'0xnew1','wallet':'0xNEW','market_id':'0xM3','market_name':'New Market','amount_usdc':5,'timestamp':1620000400}
    await m.process_trade(trade_new)

if __name__ == '__main__':
    asyncio.run(main())
