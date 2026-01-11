import asyncio
from src.polymarket_monitor.monitor import Monitor

async def main():
    m = Monitor()
    await m.store.init()
    print("Running single fetch iteration...")
    try:
        await m.run_once()
    except Exception as e:
        print("Error in run_once:", e)

if __name__ == '__main__':
    asyncio.run(main())
