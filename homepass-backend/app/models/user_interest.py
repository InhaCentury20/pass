from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "announcement_id", name="uk_user_announcement"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    announcement_id = Column(Integer, ForeignKey("Announcements.announcement_id"), nullable=False)
    created_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())

    user = relationship("User", back_populates="interests")
    announcement = relationship("Announcement")

