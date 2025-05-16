from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
from contextlib import contextmanager

# Import Base from the local models module
from db.models import Base

logger = logging.getLogger(__name__)

# Create engine with SQLite database
DATABASE_URL = 'sqlite:///bingo.db'
engine = create_engine(DATABASE_URL, echo=False)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database and create tables"""
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_db():
    """Get database session"""
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Error getting database session: {str(e)}")
        raise
    finally:
        if 'db' in locals():
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database session: {str(e)}")

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in session scope: {str(e)}")
        raise
    finally:
        db.close()
