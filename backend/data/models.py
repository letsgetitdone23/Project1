from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, index=True, nullable=False)
    locality = Column(String, index=True, nullable=True)
    cuisines = Column(Text, nullable=True)  # comma-separated list
    avg_cost_for_two = Column(Float, index=True, nullable=True)
    rating = Column(Float, index=True, nullable=True)
    votes = Column(Integer, nullable=True)
    features = Column(Text, nullable=True)  # JSON/text flags
    last_updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

