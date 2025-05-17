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

# Set up paths
# Add both current directory and parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import after path configuration
from main import main

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
