from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.database import Base


APPLICATION_STATUS = ("applied", "document_review", "won", "failed")


class Application(Base):
    __tablename__ = "Applications"

    application_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    announcement_id = Column(Integer, ForeignKey("Announcements.announcement_id"), nullable=False)
    applied_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())
    status = Column(Enum(*APPLICATION_STATUS, name="application_status"), nullable=False, default="applied")
    status_updated_at = Column(
        DateTime,
        nullable=True,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User", back_populates="applications")
    announcement = relationship("Announcement", back_populates="applications")

