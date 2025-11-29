from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    BigInteger,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class SubscriptionInfo(Base):
    __tablename__ = "SubscriptionInfo"

    info_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False, unique=True)
    bank_name = Column(String(100), nullable=True)
    join_date = Column(Date, nullable=True)
    payment_count = Column(Integer, nullable=True)
    total_payment_amount = Column(BigInteger, nullable=True)
    is_household_head = Column(Boolean, nullable=True)
    income_level_percent = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User", back_populates="subscription_info")

