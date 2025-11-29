# homepass_scraper/homepass_scraper/pipelines.py

import scrapy
from scrapy.pipelines.files import FilesPipeline
from urllib.parse import unquote, urlparse
import os
import json
import pymysql
from typing import Optional, Any, Dict
from datetime import datetime


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
        # 타이틀 필터: '공고'가 없는 제목은 DB 적재 스킵
        title = (item.get("title") or "").strip()
        if "공고" not in title:
            spider.logger.info(f"Skip DB insert: title does not contain '공고' | title='{title}'")
            return item

        # 매핑
        source_organization = item.get("department")  # 담당부서/사업자 → 출처기관으로 매핑
        source_url = item.get("post_url")
        housing_type = item.get("category")

        # 주소/지역
        address_detail = item.get("location")
        region = None  # 필요시 location에서 파싱하여 채울 수 있음

        post_date = self._parse_date(item.get("post_date"))
        application_end_date = self._parse_date(item.get("apply_date"))
        original_pdf_url = self._safe_first(item.get("file_urls", []))
        application_link = item.get("application_link")
        homepage_link = item.get("homepage_link")

        # parsed_content: 추가 필드를 JSON으로 원본 보존
        parsed_payload = {
            "intro_text": item.get("intro_text"),
            "complex_name": item.get("complex_name"),
            "supply_info": item.get("supply_info"),
            "contractor": item.get("contractor"),
            "application_link": application_link,
            "homepage_link": homepage_link,
            "contact_phone": item.get("contact_phone"),
            "contact_hours": item.get("contact_hours"),
            "attachment_name": item.get("attachment_name"),
        }
        parsed_content = json.dumps(parsed_payload, ensure_ascii=False)

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
                original_pdf_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                original_pdf_url = VALUES(original_pdf_url)
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