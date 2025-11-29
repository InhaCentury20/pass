from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationSetting(Base):
    __tablename__ = "NotificationSettings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False, unique=True)
    new_announcement = Column(Boolean, nullable=False, default=True)
    auto_apply_complete = Column(Boolean, nullable=False, default=True)
    dday = Column(Boolean, nullable=False, default=True)
    result = Column(Boolean, nullable=False, default=True)
    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User", back_populates="notification_setting")

