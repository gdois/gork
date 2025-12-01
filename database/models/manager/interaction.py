from sqlalchemy import (
    Column, Integer, String, Text,
    TIMESTAMP, func, ForeignKey
)
from sqlalchemy.orm import relationship

from database.models import Base


class Interaction(Base):
    __tablename__ = "interaction"
    __table_args__ = {"schema": "manager"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("manager.model.id"), nullable=False)
    interaction_id = Column(Integer, ForeignKey("manager.interaction.id"), nullable=True)
    command_id = Column(Integer, ForeignKey("manager.command.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("manager.agent.id"), nullable=True)
    sender = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=False)
    inserted_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    model = relationship("Model", backref="interactions")
    command = relationship("Command", backref="interactions")
    agent = relationship("Agent", backref="interactions")
    parent_interaction = relationship(
        "Interaction",
        remote_side=[id],
        backref="child_interactions",
        foreign_keys=[interaction_id]
    )