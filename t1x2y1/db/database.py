import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
def get_database_url():
    """Always use local SQLite database"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bingo_bot.db')
    return f'sqlite:///{db_path}'

# Set up logging
logger = logging.getLogger(__name__)

# Create engine
engine = None
try:
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    logger.info(f"Database engine created with URL: {DATABASE_URL}")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    global engine
    try:
        from db import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
