from __future__ import annotations

import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    BigInteger,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AutoApplyMode(str, enum.Enum):
    full_auto = "full_auto"
    approval = "approval"
    disabled = "disabled"


class Preference(Base):
    __tablename__ = "Preferences"

    pref_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False, unique=True)
    locations = Column(JSON, nullable=True)
    housing_types = Column(JSON, nullable=True)
    min_area = Column(Float, nullable=True)
    max_area = Column(Float, nullable=True)
    max_deposit = Column(BigInteger, nullable=True)
    max_monthly_rent = Column(Integer, nullable=True)
    commute_base_address = Column(String(255), nullable=True)
    max_commute_time_minutes = Column(Integer, nullable=True)
    auto_apply_mode = Column(
        Enum(AutoApplyMode), nullable=True, default=AutoApplyMode.disabled
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User", back_populates="preference")

