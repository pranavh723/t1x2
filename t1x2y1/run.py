import os
import sys
import fcntl
import psutil
import asyncio
import platform
import logging
from telegram import Update
from t1x2y1.main import main

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

LOCK_FILE = '/tmp/t1x2y1_bot.lock'
PROCESS_NAME = 'python' if platform.system() != 'Windows' else 'python.exe'

def get_running_instances():
    current_pid = os.getpid()
    instances = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if (proc.info['name'] == PROCESS_NAME and 
                't1x2y1' in ' '.join(proc.info['cmdline'] or []) and
                proc.info['pid'] != current_pid):
                instances.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return instances

def acquire_lock():
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_WRONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (IOError, OSError):
        logger.warning("Lock file exists - checking for running instances...")
        instances = get_running_instances()
        if instances:
            logger.warning(f"Found {len(instances)} running instances - terminating them")
            for proc in instances:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    continue
            os.remove(LOCK_FILE)
            return acquire_lock()
        else:
            logger.warning("No running instances found - removing stale lock")
            os.remove(LOCK_FILE)
            return acquire_lock()

async def run_bot():
    try:
        application = main()
        await application.initialize()
        await application.start()
        
        # Configure polling with conservative settings
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=2.0,  # Increased interval
            timeout=30,         # Longer timeout
            read_timeout=30     # Longer read timeout
        )
        
        logger.info("Bot started successfully")
        await application.idle()
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        raise
    finally:
        try:
            await application.stop()
        except:
            pass

if __name__ == "__main__":
    fd = None
    try:
        fd = acquire_lock()
        asyncio.run(run_bot())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if fd:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                os.remove(LOCK_FILE)
            except:
                pass
