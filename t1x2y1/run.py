#!/usr/bin/env python3
import os
import sys
import asyncio
import fcntl

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from t1x2y1.main import main

lock_file = '/tmp/t1x2y1_bot.lock'

def acquire_lock():
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (IOError, OSError):
        print("Another instance is already running. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    fd = acquire_lock()
    try:
        asyncio.run(main())
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
