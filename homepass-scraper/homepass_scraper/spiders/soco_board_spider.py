from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.spiders import Spider


class SocoBoardSpider(Spider):
    """
    Scrapes Seoul Cooperative (SOCO) board posts by iterating boardId downward.

    Usage:
        scrapy crawl soco_board_spider -a start_board_id=7000 -a days_limit=7
    """

    name = "soco_board_spider"
    allowed_domains = ["soco.seoul.go.kr"]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 2,
    }

    base_url = "https://soco.seoul.go.kr/youth/bbs/BMSR00015/view.do?menuNo=400008&boardId={board_id}"

    def __init__(self, start_board_id: int | str = 7000, days_limit: int | str = 7, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_board_id = int(start_board_id)
        self.days_limit = int(days_limit)
        # We'll stop once the post date is older than this cut-off.
        self.cutoff_date = datetime.utcnow() - timedelta(days=self.days_limit)
        self._stop_requested = False

    # --------------------------------------------------------------------- #
    # Scrapy lifecycle
    # --------------------------------------------------------------------- #
    def start_requests(self) -> Iterable[Request]:
        if self.current_board_id <= 0:
            self.logger.warning("Invalid starting board id: %s", self.current_board_id)
            return
        yield self._build_request(self.current_board_id)

    def _build_request(self, board_id: int) -> Request:
        url = self.base_url.format(board_id=board_id)
        return Request(
            url=url,
            callback=self.parse_post,
            errback=self._handle_error,
            cb_kwargs={"board_id": board_id},
            dont_filter=True,
        )

    def _handle_error(self, failure, board_id: int):
        self.logger.warning("Failed to fetch board %s: %s", board_id, failure.value)
        next_id = board_id - 1
        if not self._stop_requested and next_id > 0:
            yield self._build_request(next_id)

    # --------------------------------------------------------------------- #
    # Parsing helpers
    # --------------------------------------------------------------------- #
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

    def _extract_files(self, response: scrapy.http.Response) -> tuple[list[str], list[str]]:
        file_urls: list[str] = []
        attachment_names: list[str] = []
        for anchor in response.css("a[href*='fileDown']"):
            href = anchor.attrib.get("href")
            if not href:
                continue
            file_urls.append(response.urljoin(href))
            name = anchor.css("::text").get()
            if name:
                attachment_names.append(name.strip())
        return file_urls, attachment_names

    # --------------------------------------------------------------------- #
    # Parse response
    # --------------------------------------------------------------------- #
    def parse_post(self, response: scrapy.http.Response, board_id: int):
        title = self._extract_title(response)
        post_date = self._extract_date(response)

        if post_date and post_date < self.cutoff_date:
            self.logger.info(
                "Post %s is older than cutoff (%s < %s). Stopping scrape.",
                board_id,
                post_date.date(),
                self.cutoff_date.date(),
            )
            self._stop_requested = True
            return

        file_urls, attachment_names = self._extract_files(response)

        item = {
            "title": title,
            "department": self._extract_department(response),
            "post_url": response.url,
            "category": "",
            "location": "",
            "post_date": post_date.strftime("%Y-%m-%d") if post_date else None,
            "apply_date": None,
            "file_urls": file_urls,
            "application_link": response.url,
            "homepage_link": response.url,
            "attachment_name": attachment_names[0] if attachment_names else None,
            "intro_text": None,
            "complex_name": None,
            "supply_info": None,
            "contractor": None,
        }
        yield item

        next_id = board_id - 1
        if not self._stop_requested and next_id > 0:
            yield self._build_request(next_id)


