from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, VARBINARY, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    rrn_encrypted = Column(VARBINARY(255), nullable=True)
    rrn_key_encrypted = Column(VARBINARY(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(
        DateTime, nullable=True, server_default=func.current_timestamp()
    )

    subscription_info = relationship(
        "SubscriptionInfo", back_populates="user", uselist=False
    )
    preference = relationship("Preference", back_populates="user", uselist=False)
    notification_setting = relationship(
        "NotificationSetting", back_populates="user", uselist=False
    )
    applications = relationship("Application", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")


