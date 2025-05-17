#!/usr/bin/env python3
import os
import sys
import asyncio

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

import asyncio
from t1x2y1.main import main

if __name__ == "__main__":
    asyncio.run(main())
