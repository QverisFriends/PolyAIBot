import asyncio
from src.polymarket_monitor.monitor import Monitor

async def main():
    m = Monitor()
    await m.run()

if __name__ == '__main__':
    asyncio.run(main())
