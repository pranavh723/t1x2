import asyncio
from t1x2y1.main import main

async def run_bot():
    try:
        await main()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())
