from sqlalchemy import (
    Column, Integer, String, Text,
    TIMESTAMP, func
)
from sqlalchemy.orm import relationship

from database.models import Base


class Group(Base):
    __tablename__ = "group"
    __table_args__ = {"schema": "base"}

    id = Column(Integer, primary_key=True)
    src_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255))
    description = Column(Text)
    profile_image_url = Column(Text)

    inserted_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    messages = relationship("Message", back_populates="group")
    remembers = relationship("Remember", back_populates="group")
