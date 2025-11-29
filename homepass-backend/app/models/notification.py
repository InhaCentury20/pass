from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Notification(Base):
    __tablename__ = "Notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    announcement_id = Column(Integer, ForeignKey("Announcements.announcement_id"), nullable=True)
    message = Column(String(500), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())

    user = relationship("User", back_populates="notifications")
    announcement = relationship("Announcement", back_populates="notifications")

