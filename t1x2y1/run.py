#!/usr/bin/env python3
import os
import sys
import asyncio
import fcntl
import psutil

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from t1x2y1.main import main

LOCK_FILE = '/tmp/t1x2y1_bot.lock'
PROCESS_NAME = 'python'  # Or your specific process name

def kill_previous_instances():
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if (PROCESS_NAME in proc.info['name'].lower() and 
                't1x2y1' in ' '.join(proc.info['cmdline'] or []) and
                proc.info['pid'] != current_pid):
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def acquire_lock():
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_WRONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (IOError, OSError):
        print("Another instance is already running. Killing it...")
        kill_previous_instances()
        os.remove(LOCK_FILE)
        return acquire_lock()  # Retry

if __name__ == "__main__":
    kill_previous_instances()  # Force cleanup first
    fd = acquire_lock()
    try:
        asyncio.run(main())
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            os.remove(LOCK_FILE)
        except:
            pass
