import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Add the project root directory to the Python path for deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# Database configuration from environment variables
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db/bingo_bot.db')

# Set up logging
logger = logging.getLogger(__name__)

# Create engine
try:
    # Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
    os.makedirs(db_dir, exist_ok=True)
    
    engine = create_engine(DATABASE_URL)
    logger.info(f"Database engine created with URL: {DATABASE_URL}")
    
    # Initialize database on startup
    init_db()
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered with Base
        import sys
        import importlib
        
        # Import models directly
        from db import models
        logger.info("Successfully imported models from local db package")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
