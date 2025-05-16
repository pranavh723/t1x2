import os
import sys
import logging
from sqlalchemy import create_engine, inspect
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
    """Initialize database tables with verification"""
    try:
        from t1x2y1.db.models import Base, User, Room, Game, Card, Maintenance, Player
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info(f"Created tables: {Base.metadata.tables.keys()}")
        
        # Verify tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables: {existing_tables}")
        
        # Create critical tables if missing
        required_tables = ['users', 'rooms', 'games', 'cards', 'maintenance', 'players']
        for table in required_tables:
            if table not in existing_tables:
                logger.warning(f"Creating missing table: {table}")
                if table == 'users':
                    User.__table__.create(bind=engine)
                elif table == 'rooms':
                    Room.__table__.create(bind=engine)
                elif table == 'games':
                    Game.__table__.create(bind=engine)
                elif table == 'cards':
                    Card.__table__.create(bind=engine)
                elif table == 'maintenance':
                    Maintenance.__table__.create(bind=engine)
                elif table == 'players':
                    Player.__table__.create(bind=engine)
                
        return True
    except Exception as e:
        logger.error(f"Database init failed: {e}", exc_info=True)
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
