from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

# Create engine
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bingo_bot.db')
engine = create_engine(DATABASE_URL)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create tables"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise e

def get_db():
    """Get database session"""
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        try:
            db.close()
        except:
            pass
