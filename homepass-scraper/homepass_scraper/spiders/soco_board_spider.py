from __future__ import annotations

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import pymysql

import scrapy
from scrapy import FormRequest, Request
from scrapy.spiders import Spider


class SocoBoardSpider(Spider):
    """
    Scrapes the SOCO 청년안심주택 모집공고 게시판.

    - Fetches list pages (same JSON API as the website)
    - Extracts the visible "번호" (td) value
    - Stops when the number is less than or equal to the saved checkpoint
    """

    name = "soco_board_spider"
    allowed_domains = ["soco.seoul.go.kr"]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.4,
        "CONCURRENT_REQUESTS": 2,
    }

    list_url = "https://soco.seoul.go.kr/youth/pgm/home/yohome/bbsListJson.json"
    detail_url = "https://soco.seoul.go.kr/youth/bbs/BMSR00015/view.do?menuNo=400008&boardId={board_id}"

    def __init__(
        self,
        last_checkpoint_file: str | None = None,
        db_host: str | None = None,
        db_port: int | str = 3306,
        db_user: str | None = None,
        db_password: str | None = None,
        db_name: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        default_path = Path(__file__).resolve().parents[2] / "last_scraped_no.txt"
        self.checkpoint_path = Path(last_checkpoint_file).resolve() if last_checkpoint_file else default_path
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_host = db_host or os.environ.get("DB_HOST", "century20-rds.clqcgo84gd3x.us-west-2.rds.amazonaws.com")
        self.db_port = int(db_port or os.environ.get("DB_PORT", 3306))
        self.db_user = db_user or os.environ.get("DB_USER", "admin")
        self.db_password = db_password or os.environ.get("DB_PASSWORD", "century20!")
        self.db_name = db_name or os.environ.get("DB_NAME", "century20")

        self.last_scraped_no = self._load_checkpoint()
        self.current_max_no = self.last_scraped_no
        self.logger.info("Loaded last scraped number: %s", self.last_scraped_no)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def _load_checkpoint(self) -> int:
        db_value = self._fetch_latest_listing_number()
        if db_value is not None:
            return db_value
        if self.checkpoint_path.exists():
            try:
                return int(self.checkpoint_path.read_text().strip())
            except ValueError:
                pass
        return 0

    def _fetch_latest_listing_number(self) -> Optional[int]:
        try:
            connection = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                db=self.db_name,
                cursorclass=pymysql.cursors.DictCursor,
            )
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT listing_number
                        FROM Announcements
                        WHERE listing_number IS NOT NULL
                        ORDER BY listing_number DESC
                        LIMIT 1
                        """
                    )
                    row = cursor.fetchone()
                    if row and row.get("listing_number") is not None:
                        return int(row["listing_number"])
        except Exception as exc:
            self.logger.error("Failed to fetch listing_number from DB: %s", exc)
        return None

    def start_requests(self) -> Iterable[FormRequest]:
        yield self._build_list_request(page=1)

    def _build_list_request(self, page: int) -> FormRequest:
        formdata = {
            "bbsId": "BMSR00015",
            "pageIndex": str(page),
            "searchAdresGu": "",
            "searchCondition": "",
            "searchKeyword": "",
            "optn2": "",
            "optn5": "",
        }
        return FormRequest(
            url=self.list_url,
            formdata=formdata,
            callback=self.parse_list,
            cb_kwargs={"page": page},
        )

    # ------------------------------------------------------------------ #
    # List parsing
    # ------------------------------------------------------------------ #
    def parse_list(self, response: scrapy.http.Response, page: int):
        data = json.loads(response.text)
        result_list = data.get("resultList") or []
        paging = data.get("pagingInfo") or {}

        tot_row = int(paging.get("totRow", 0))
        row_start = int(paging.get("rowStart", 0))
        stop_crawling = False

        for idx, row in enumerate(result_list):
            number = tot_row - row_start - idx
            board_id = row.get("boardId")

            if number <= self.last_scraped_no:
                self.logger.info(
                    "Reached previously scraped number (current: %s, checkpoint: %s). Stopping.",
                    number,
                    self.last_scraped_no,
                )
                stop_crawling = True
                break

            self.current_max_no = max(self.current_max_no, number)
            detail_url = self.detail_url.format(board_id=board_id)

            yield Request(
                url=detail_url,
                callback=self.parse_detail,
                cb_kwargs={
                    "board_id": board_id,
                    "list_number": number,
                    "row": row,
                },
            )

        if not stop_crawling:
            page_index = int(paging.get("pageIndex", page))
            tot_page = int(paging.get("totPage", page))
            if page_index < tot_page:
                yield self._build_list_request(page=page_index + 1)

    # ------------------------------------------------------------------ #
    # Detail parsing helpers
    # ------------------------------------------------------------------ #
    def _extract_title(self, response: scrapy.http.Response) -> str:
        title = response.css('meta[property="og:title"]::attr(content)').get()
        if title:
            return title.strip()
        title = response.css("title::text").get()
        return title.strip() if title else response.url

    def _extract_department(self, response: scrapy.http.Response) -> str | None:
        text = " ".join(response.css("body *::text").getall())
        match = re.search(r"(담당부서|담당자)\s*[:：]\s*([^\s]+)", text)
        return match.group(2).strip() if match else None

    def _extract_date(self, response: scrapy.http.Response) -> datetime | None:
        text = response.text
        match = re.search(r"(\d{4})[.\-](\d{2})[.\-](\d{2})", text)
        if not match:
            return None
        year, month, day = map(int, match.groups())
        try:
            return datetime(year, month, day)
        except ValueError:
            return None

    def parse_detail(self, response: scrapy.http.Response, board_id: int, list_number: int, row: dict):
        title = row.get("nttSj") or self._extract_title(response)
        department = row.get("optn3") or self._extract_department(response)

        post_date_text = row.get("ntceBgnde") or self._extract_table_value(response, "공고게시일")
        apply_date_text = row.get("optn4") or self._extract_table_value(response, "청약신청일")

        category_text = self._build_category_label(row) or self._extract_table_value(response, "카테고리")

        item = {
            "title": title,
            "department": department,
            "post_url": response.url,
            "category": category_text,
            "location": "",
            "post_date": self._clean_date(post_date_text),
            "apply_date": self._clean_date(apply_date_text),
            "application_link": self._extract_application_link(response),
            "homepage_link": self._extract_homepage_link(response),
            "original_pdf_url": self._extract_pdf_link(response),
            "intro_text": None,
            "complex_name": None,
            "supply_info": None,
            "contractor": row.get("optn3"),
            "listing_number": list_number,
            "board_id": board_id,
        }
        yield item

    def _clean_date(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        value = value.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return value

    def _extract_table_value(self, response: scrapy.http.Response, label: str) -> Optional[str]:
        xpath = f'//th[contains(normalize-space(), "{label}")]/following-sibling::td[1]//text()'
        texts = response.xpath(xpath).getall()
        cleaned = " ".join(t.strip() for t in texts if t.strip())
        return cleaned or None

    def _build_category_label(self, row: dict) -> Optional[str]:
        labels: List[str] = []
        type_map = {"1": "공공", "2": "민간"}
        stage_map = {"1": "최초", "2": "추가"}
        cat_type = (row.get("optn2") or "").strip()
        stage = (row.get("optn5") or "").strip()
        if cat_type in type_map:
            labels.append(type_map[cat_type])
        if stage in stage_map:
            labels.append(stage_map[stage])
        if not labels and row.get("optn2Nm"):
            labels.append(row.get("optn2Nm"))
        return " ".join(labels) if labels else None

    def _extract_application_link(self, response: scrapy.http.Response) -> Optional[str]:
        link = response.xpath('//p[contains(., "청약신청 페이지")]//a/@href').get()
        return response.urljoin(link) if link else None

    def _extract_homepage_link(self, response: scrapy.http.Response) -> Optional[str]:
        link = response.xpath('//p[contains(., "단지 홈페이지")]//a/@href').get()
        return response.urljoin(link) if link else None

    def _extract_pdf_link(self, response: scrapy.http.Response) -> Optional[str]:
        href = response.css('ul.view_data span.file a[href*="fileDown.do"]::attr(href)').get()
        return response.urljoin(href) if href else None

    # ------------------------------------------------------------------ #
    # Shutdown
    # ------------------------------------------------------------------ #
    def closed(self, reason: str):
        try:
            self.checkpoint_path.write_text(str(self.current_max_no))
            self.logger.info("Saved checkpoint %s to %s", self.current_max_no, self.checkpoint_path)
        except OSError as exc:
            self.logger.error("Failed to save checkpoint: %s", exc)


