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

# Import DATABASE_URL from config
try:
    from t1x2y1.config import DATABASE_URL
except ImportError:
    try:
        from config import DATABASE_URL
    except ImportError:
        DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///bingo.db')

# Set up logging
logger = logging.getLogger(__name__)

# Create engine
try:
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
    try:
        # Import all models to ensure they're registered with Base
        import sys
        import importlib
        
        # Try to import models using both possible import paths
        try:
            from t1x2y1.db import models
            logger.info("Successfully imported models from t1x2y1.db")
        except ImportError:
            try:
                from db import models
                logger.info("Successfully imported models from db")
            except ImportError:
                logger.error("Could not import models from any path")
        
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
