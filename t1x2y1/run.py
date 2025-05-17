#!/usr/bin/env python3
import os
import sys
import logging
import asyncio

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Package import
from t1x2y1.main import main

async def run_bot():
    try:
        logger.info("Starting application...")
        await main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(run_bot())
