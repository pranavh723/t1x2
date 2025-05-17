from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Maintenance(Base):
    """Maintenance mode settings"""
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    message = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "message": self.message,
            "last_updated": self.last_updated.isoformat()
        }
