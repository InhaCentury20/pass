# homepass_scraper/homepass_scraper/pipelines.py

import scrapy
from scrapy.pipelines.files import FilesPipeline
from urllib.parse import unquote, urlparse
import os
import json
import pymysql
from typing import Optional, Any, Dict, List
from datetime import datetime
import re


class HomepassScraperPipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        """
        아이템의 file_urls를 가져와 요청을 생성합니다.
        원본 파일 이름을 메타(meta) 데이터에 저장합니다.
        """
        for file_url in item.get('file_urls', []):
            try:
                # 1. 스파이더가 추출한 원본 파일 이름을 가져옵니다.
                #    (이 작업을 위해 스파이더 코드도 수정해야 합니다.)
                original_filename = item['attachment_name']

                # 2. 요청에 원본 파일 이름을 'meta'로 함께 넘깁니다.
                yield scrapy.Request(file_url, meta={'original_filename': original_filename})
            except Exception as e:
                info.spider.logger.warning(f"Failed to get file URL: {e} - item: {item}")

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        다운로드된 파일의 저장 경로와 '원본 파일 이름'을 반환합니다.
        """
        try:
            # 3. get_media_requests의 meta에서 원본 파일 이름을 가져옵니다.
            original_filename = request.meta.get('original_filename')

            if original_filename:
                # 4. 'full/' 폴더 대신 원본 파일 이름으로 바로 저장하도록 반환
                #    (필요하다면 'full/' + original_filename 으로 해도 됩니다)
                return original_filename

        except Exception as e:
            info.spider.logger.warning(f"Failed to set file path: {e}")

        # 5. 실패 시 Scrapy 기본 방식(해시)을 따릅니다.
        return super().file_path(request, response, info, item=item)


class MySQLAnnouncementsPipeline:
    """
    Scrapy Item을 MySQL RDS 테이블 'Announcements'에 적재합니다.
    환경변수 기본값은 사용자가 제공한 RDS 정보를 따릅니다.
    """

    def __init__(self):
        self.host = os.environ.get("DB_HOST", "century20-rds.clqcgo84gd3x.us-west-2.rds.amazonaws.com")
        self.port = int(os.environ.get("DB_PORT", "3306"))
        self.user = os.environ.get("DB_USER", "admin")
        self.password = os.environ.get("DB_PASSWORD", "century20!")
        self.database = os.environ.get("DB_NAME", "century20")
        self.table = os.environ.get("DB_TABLE", "Announcements")
        self.conn = None
        self.cur = None
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            self._apply_database_url(database_url)

    @staticmethod
    def _safe_first(seq, default=None):
        if not seq:
            return default
        return seq[0]

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        v = value.strip()
        # 기대 포맷 예: '2025-11-10' 또는 '2025-11-10 00:00:00'
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(v, fmt)
                # datetime 컬럼으로 저장
                if fmt == "%Y-%m-%d":
                    return datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                return dt
            except ValueError:
                continue
        return None

    def _apply_database_url(self, database_url: str) -> None:
        try:
            parsed = urlparse(database_url)
        except Exception:
            return
        if not parsed.scheme or not parsed.scheme.startswith("mysql"):
            return
        if parsed.hostname:
            self.host = parsed.hostname
        if parsed.port:
            self.port = parsed.port
        if parsed.username:
            self.user = unquote(parsed.username)
        if parsed.password:
            self.password = unquote(parsed.password)
        if parsed.path and len(parsed.path) > 1:
            self.database = parsed.path.lstrip("/")

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        return value.copy() if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            cleaned = re.sub(r"[^\d\-]", "", value)
            if not cleaned:
                return None
            try:
                return int(cleaned)
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_bool(value: Any) -> Optional[bool]:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(int(value))
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "y", "yes", "t", "on"}:
                return True
            if normalized in {"0", "false", "n", "no", "f", "off"}:
                return False
        return None

    @staticmethod
    def _sanitize_str(value: Any) -> Optional[str]:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None

    @staticmethod
    def _ensure_list_of_str(value: Any) -> List[str]:
        if isinstance(value, list):
            result: List[str] = []
            for item in value:
                if isinstance(item, str):
                    stripped = item.strip()
                    if stripped:
                        result.append(stripped)
            return result
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _ensure_list_of_dict(value: Any) -> List[Dict[str, Any]]:
        if isinstance(value, list):
            return [entry for entry in value if isinstance(entry, dict)]
        return []

    @staticmethod
    def _json_or_none(value: Any) -> Optional[str]:
        if value in (None, [], {}):
            return None
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return None

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
        self.cur = self.conn.cursor()
        spider.logger.info(f"MySQL connected host={self.host} db={self.database} table={self.table}")

    def close_spider(self, spider):
        try:
            if self.conn:
                self.conn.commit()
        finally:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()

    def process_item(self, item: Dict[str, Any], spider):
        # 타이틀 필터: 특정 키워드가 없으면 건너뜀
        title = (item.get("title") or "").strip()
        allowed_keywords = ("공고", "청년안심주택")
        if not any(keyword in title for keyword in allowed_keywords):
            spider.logger.info(
                f"Skip DB insert: title does not contain {allowed_keywords} | title='{title}'"
            )
            return item

        parsed_payload = self._as_dict(item.get("parsed_content"))

        def pick_value(key: str) -> Any:
            value = item.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                return parsed_payload.get(key)
            return value

        # 매핑
        source_organization = self._sanitize_str(pick_value("department")) or self._sanitize_str(
            pick_value("source_organization")
        )
        source_url = self._sanitize_str(pick_value("post_url")) or self._sanitize_str(pick_value("source_url"))
        housing_type = self._sanitize_str(pick_value("category")) or self._sanitize_str(pick_value("housing_type"))

        # 주소/지역
        address_detail = self._sanitize_str(pick_value("location")) or self._sanitize_str(pick_value("address_detail"))
        region = self._sanitize_str(pick_value("region"))

        post_date = self._parse_date(pick_value("post_date") or item.get("post_date"))
        application_end_date = self._parse_date(pick_value("apply_date") or item.get("apply_date"))
        original_pdf_url = self._sanitize_str(pick_value("original_pdf_url"))
        application_link = self._sanitize_str(pick_value("application_link"))
        homepage_link = self._sanitize_str(pick_value("homepage_link"))

        # 부가 텍스트 필드들을 parsed_content에 병합
        for field in (
            "intro_text",
            "complex_name",
            "supply_info",
            "contractor",
            "contact_phone",
            "contact_hours",
            "attachment_name",
        ):
            value = self._sanitize_str(pick_value(field))
            if value is not None:
                parsed_payload[field] = value
        if application_link:
            parsed_payload["application_link"] = application_link
        if homepage_link:
            parsed_payload["homepage_link"] = homepage_link

        # 수치/JSON 필드 정규화
        min_deposit = self._normalize_int(pick_value("min_deposit"))
        max_deposit = self._normalize_int(pick_value("max_deposit"))
        monthly_rent = self._normalize_int(pick_value("monthly_rent"))
        total_households = self._normalize_int(pick_value("total_households"))
        commute_time = self._normalize_int(pick_value("commute_time"))
        eligibility = self._sanitize_str(pick_value("eligibility"))
        commute_base_address = self._sanitize_str(pick_value("commute_base_address"))
        is_customized_flag = self._normalize_bool(pick_value("is_customized"))
        image_urls = self._ensure_list_of_str(pick_value("image_urls"))
        schedules = self._ensure_list_of_dict(pick_value("schedules"))
        listing_number = self._normalize_int(item.get("listing_number"))

        for key, value in (
            ("min_deposit", min_deposit),
            ("max_deposit", max_deposit),
            ("monthly_rent", monthly_rent),
            ("total_households", total_households),
            ("commute_time", commute_time),
            ("eligibility", eligibility),
            ("commute_base_address", commute_base_address),
        ):
            if value is not None:
                parsed_payload[key] = value
        if is_customized_flag is not None:
            parsed_payload["is_customized"] = is_customized_flag
        if image_urls:
            parsed_payload["image_urls"] = image_urls
        if schedules:
            parsed_payload["schedules"] = schedules

        parsed_content = json.dumps(parsed_payload, ensure_ascii=False)
        image_urls_json = self._json_or_none(image_urls)
        schedules_json = self._json_or_none(schedules)
        is_customized_db = int(is_customized_flag) if isinstance(is_customized_flag, bool) else None

        sql = f"""
            INSERT INTO {self.table}
            (
                title,
                source_organization,
                source_url,
                housing_type,
                region,
                address_detail,
                post_date,
                application_end_date,
                application_link,
                homepage_link,
                parsed_content,
                original_pdf_url,
                min_deposit,
                max_deposit,
                monthly_rent,
                total_households,
                eligibility,
                commute_base_address,
                commute_time,
                is_customized,
                image_urls,
                schedules,
                listing_number
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                source_organization = VALUES(source_organization),
                source_url = VALUES(source_url),
                housing_type = VALUES(housing_type),
                region = VALUES(region),
                address_detail = VALUES(address_detail),
                post_date = VALUES(post_date),
                application_end_date = VALUES(application_end_date),
                application_link = VALUES(application_link),
                homepage_link = VALUES(homepage_link),
                parsed_content = VALUES(parsed_content),
                original_pdf_url = VALUES(original_pdf_url),
                min_deposit = VALUES(min_deposit),
                max_deposit = VALUES(max_deposit),
                monthly_rent = VALUES(monthly_rent),
                total_households = VALUES(total_households),
                eligibility = VALUES(eligibility),
                commute_base_address = VALUES(commute_base_address),
                commute_time = VALUES(commute_time),
                is_customized = VALUES(is_customized),
                image_urls = VALUES(image_urls),
                schedules = VALUES(schedules),
                listing_number = VALUES(listing_number)
        """
        params = (
            title,
            source_organization,
            source_url,
            housing_type,
            region,
            address_detail,
            post_date.strftime("%Y-%m-%d %H:%M:%S") if post_date else None,
            application_end_date.strftime("%Y-%m-%d %H:%M:%S") if application_end_date else None,
            application_link,
            homepage_link,
            parsed_content,
            original_pdf_url,
            min_deposit,
            max_deposit,
            monthly_rent,
            total_households,
            eligibility,
            commute_base_address,
            commute_time,
            is_customized_db,
            image_urls_json,
            schedules_json,
            listing_number,
        )

        try:
            affected = self.cur.execute(sql, params)
            self.conn.commit()
            spider.logger.info(f"MySQL upsert ok (affected={affected}) title='{title}' post_date='{post_date}'")
        except Exception as e:
            spider.logger.error(f"MySQL insert failed: {e} | item={item}")
            self.conn.rollback()
            # 데이터 손실을 막기 위해 예외를 다시 던지지 않고 통과
        return item