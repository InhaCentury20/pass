from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Announcement(Base):
    __tablename__ = "Announcements"

    announcement_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    source_organization = Column(String(100), nullable=True)
    source_url = Column(String(2048), nullable=True)
    housing_type = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    address_detail = Column(String(255), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    application_end_date = Column(DateTime, nullable=True)
    application_link = Column(String(2048), nullable=True)
    homepage_link = Column(String(2048), nullable=True)
    parsed_content = Column(Text, nullable=True)
    original_pdf_url = Column(String(2048), nullable=True)
    scraped_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())
    image_urls_json = Column("image_urls", JSON, nullable=True)
    schedules_json = Column("schedules", JSON, nullable=True)
    price_json = Column("price", JSON, nullable=True)
    # DB 컬럼은 프로퍼티와 이름 충돌을 피하기 위해 *_db로 보관
    min_deposit_db = Column("min_deposit", Integer, nullable=True)
    monthly_rent_db = Column("monthly_rent", Integer, nullable=True)
    max_deposit_db = Column("max_deposit", Integer, nullable=True)
    total_households_db = Column("total_households", Integer, nullable=True)
    eligibility_db = Column("eligibility", String(255), nullable=True)
    commute_base_address_db = Column("commute_base_address", String(255), nullable=True)
    commute_time_db = Column("commute_time", Integer, nullable=True)
    is_customized_db = Column("is_customized", Integer, nullable=True)

    applications = relationship("Application", back_populates="announcement")
    notifications = relationship("Notification", back_populates="announcement")

    # Convenience helpers -------------------------------------------------
    def load_parsed_content(self) -> Dict[str, Any]:
        if not self.parsed_content:
            return {}
        try:
            return json.loads(self.parsed_content)
        except json.JSONDecodeError:
            return {}

    @property
    def image_urls(self) -> List[str]:
        if isinstance(self.image_urls_json, list):
            return [u for u in self.image_urls_json if isinstance(u, str)]
        data = self.load_parsed_content()
        images = data.get("image_urls", [])
        return images if isinstance(images, list) else []

    @property
    def min_deposit(self) -> Optional[int]:
        # 1) DB 컬럼 우선
        value = self.min_deposit_db
        if isinstance(value, (int, float)):
            return int(value)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("min_deposit")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def max_deposit(self) -> Optional[int]:
        # 1) DB 컬럼 우선
        value = self.max_deposit_db
        if isinstance(value, (int, float)):
            return int(value)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("max_deposit")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def monthly_rent(self) -> Optional[int]:
        # 1) DB 컬럼 우선
        value = self.monthly_rent_db
        if isinstance(value, (int, float)):
            return int(value)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("monthly_rent")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def is_customized(self) -> bool:
        # 1) DB 컬럼 우선
        if self.is_customized_db is not None:
            return bool(int(self.is_customized_db))
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        return bool(data.get("is_customized", False))

    @property
    def total_households(self) -> Optional[int]:
        # 1) DB 컬럼 우선
        value = self.total_households_db
        if isinstance(value, (int, float)):
            return int(value)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("total_households")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def eligibility(self) -> Optional[str]:
        # 1) DB 컬럼 우선
        if self.eligibility_db:
            return str(self.eligibility_db)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("eligibility")
        return str(value) if value else None

    @property
    def commute_base_address(self) -> Optional[str]:
        # 1) DB 컬럼 우선
        if self.commute_base_address_db:
            return str(self.commute_base_address_db)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("commute_base_address")
        return str(value) if value else None

    @property
    def commute_time(self) -> Optional[int]:
        # 1) DB 컬럼 우선
        value = self.commute_time_db
        if isinstance(value, (int, float)):
            return int(value)
        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        value = data.get("commute_time")
        return int(value) if isinstance(value, (int, float)) else None

    @staticmethod
    def _normalize_price_option(raw: dict) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None

        def first(*keys):
            for key in keys:
                if key in raw and raw[key] not in (None, ""):
                    return raw[key]
            return None

        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        normalized = {
            "type": first("타입", "type"),
            "deposit_ratio": first("보증금%", "deposit_ratio"),
            "supply_type_primary": first("공급유형1", "supply_type_primary"),
            "supply_type_secondary": first("공급유형2", "supply_type_secondary"),
            "predicted_tier": first("예측경쟁률", "predicted_tier"),
            "deposit_amount": to_float(first("보증금(만원)", "deposit_amount")),
            "rent_amount": to_float(first("임대료(만원)", "rent_amount")),
        }

        if all(value in (None, "") for value in normalized.values()):
            return None

        return normalized

    @property
    def price(self) -> List[Dict[str, Any]]:
        def normalize(value: Any) -> List[Dict[str, Any]]:
            result: List[Dict[str, Any]] = []
            if isinstance(value, list):
                for item in value:
                    normalized = self._normalize_price_option(item)
                    if normalized:
                        result.append(normalized)
                return result
            if isinstance(value, str) and value.strip():
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    return result
                return normalize(parsed)
            return result

        normalized = normalize(self.price_json)
        if normalized:
            return normalized
        data = self.load_parsed_content()
        return normalize(data.get("price"))

    @property
    def schedules(self) -> List[Dict[str, Any]]:
        def _normalize(value: Any) -> List[Dict[str, Any]]:
            result: List[Dict[str, Any]] = []

            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        event = item.get("event") or item.get("title")
                        date = item.get("date") or item.get("value")
                        if event or date:
                            result.append(
                                {
                                    "event": str(event) if event is not None else f"일정 {idx + 1}",
                                    "date": str(date) if date is not None else None,
                                }
                            )
                return result

            if isinstance(value, dict):
                for key, raw in value.items():
                    if key or raw:
                        result.append(
                            {
                                "event": str(key) if key is not None else "일정",
                                "date": str(raw) if raw is not None else None,
                            }
                        )
                return result

            if isinstance(value, str) and value.strip():
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    result.append({"event": "주요 일정", "date": value})
                    return result
                return _normalize(parsed)

            return result

        # 1) DB 컬럼 우선
        normalized = _normalize(self.schedules_json)
        if normalized:
            return normalized

        # 2) fallback: parsed_content
        data = self.load_parsed_content()
        return _normalize(data.get("schedules"))

