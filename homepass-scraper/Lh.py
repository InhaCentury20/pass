import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pymysql
import requests
from urllib.parse import urlencode, unquote

BASE_URL = "https://apis.data.go.kr/B552555/lhLeaseNoticeInfo1/lhLeaseNoticeInfo1"


def fetch_lh_notices(
    service_key: str,
    page_size: int,
    page: int,
    post_date: Optional[str] = None,
    close_date: Optional[str] = None,
) -> Any:
    params = {
        "ServiceKey": service_key,
        "PG_SZ": page_size,
        "PAGE": page,
    }
    if post_date:
        params["PAN_NT_ST_DT"] = post_date
    if close_date:
        params["CLSG_DT"] = close_date

    url = f"{BASE_URL}?{urlencode(params)}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def extract_items(payload: Any) -> List[Dict[str, Any]]:
    """LH API 응답 구조(dsSch, dsList 등)를 모두 순회해 실제 공고(dict)의 리스트로 평탄화."""

    collected: List[Dict[str, Any]] = []

    def traverse(node: Any) -> None:
        if isinstance(node, list):
            for element in node:
                traverse(element)
            return

        if not isinstance(node, dict):
            return

        # 실제 공고 레코드로 판단되면 수집
        if "PAN_NM" in node and "DTL_URL" in node:
            collected.append(node)

        # 중첩 구조를 계속 탐색
        for value in node.values():
            if isinstance(value, (list, dict)):
                traverse(value)

    traverse(payload)
    return collected


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y.%m.%d")
    except ValueError:
        return None


def normalize_notice(item: Dict[str, Any]) -> Dict[str, Any]:
    application_end = None
    if item.get("PAN_SS") != "상담요청":
        application_end = parse_date(item.get("CLSG_DT"))

    return {
        "title": item.get("PAN_NM"),
        "source_organization": "LH",
        "source_url": item.get("DTL_URL"),
        "housing_type": item.get("AIS_TP_CD_NM"),
        "region": item.get("CNP_CD_NM"),
        "post_date": parse_date(item.get("PAN_NT_ST_DT")),
        "application_end_date": application_end,
        "listing_number": None,
        "application_link": item.get("DTL_URL") or None,
    }


def upsert_announcements(records: List[Dict[str, Any]]) -> None:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "century20-rds.clqcgo84gd3x.us-west-2.rds.amazonaws.com"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "century20!"),
        database=os.getenv("DB_NAME", "century20"),
        charset="utf8mb4",
    )
    sql = """
    INSERT INTO Announcements
        (title, source_organization, source_url, housing_type,
         region, post_date, application_end_date,
         listing_number, application_link)
    VALUES (%(title)s, %(source_organization)s, %(source_url)s, %(housing_type)s,
            %(region)s, %(post_date)s, %(application_end_date)s,
            %(listing_number)s, %(application_link)s)
    ON DUPLICATE KEY UPDATE
        source_url = VALUES(source_url),
        housing_type = VALUES(housing_type),
        region = VALUES(region),
        post_date = VALUES(post_date),
        application_end_date = VALUES(application_end_date),
        application_link = VALUES(application_link)
    """
    try:
        with conn.cursor() as cur:
            cur.executemany(sql, records)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    encoded_key = os.environ.get(
        "LH_SERVICE_KEY",
        "HrHXtmZG19lK%2BUXcp7LXicSFsrkQis3i5U6PwgX46ZWiWfcro6BaNNKOW94EPEPb2zLQ2ti4KdtpZkVwqGN0yg%3D%3D",
    )
    service_key = unquote(encoded_key)

    raw = fetch_lh_notices(
        service_key=service_key,
        page_size=50,
        page=1,
        post_date="2024.10.01",
        close_date="2024.10.31",
    )
    items = extract_items(raw)
    print(f"LH API items count: {len(items)}")
    if items:
        print("첫 번째 항목 예시:", items[0])

    normalized = [normalize_notice(item) for item in items if item.get("PAN_NM")]
    if normalized:
        upsert_announcements(normalized)
        print(f"{len(normalized)}건 저장 완료")
    else:
        print("저장할 데이터 없음")