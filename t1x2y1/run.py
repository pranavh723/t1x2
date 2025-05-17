#!/usr/bin/env python3
import os
import sys
import asyncio

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from t1x2y1.main import main

if __name__ == "__main__":
    try:
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bot
        loop.run_until_complete(main())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        loop.close()
