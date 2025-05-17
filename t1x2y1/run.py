#!/usr/bin/env python3
import os
import sys
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import after path configuration
from t1x2y1.main import main

try:
    logger.info("Starting application...")
    main()
except Exception as e:
    logger.error(f"Application failed: {e}", exc_info=True)
    sys.exit(1)
