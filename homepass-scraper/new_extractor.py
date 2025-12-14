import json
import pdfplumber
import pandas as pd
import re
import io
import pymysql
import requests
from predictor import preprocess_and_predict_group, load_model_assets


class AnsimJutaekParser:

    def __init__(self):
        self.all_data = []
        self.error_logs = []
        self.qualifications = {}

    def update_row(self, row, cursor):
        self.all_data = []
        self.qualifications = {}

        parsed_content_raw = row["parsed_content"]

        board_text = ""
        if parsed_content_raw:
            if isinstance(parsed_content_raw, str):
                try:
                    parsed_content_dict = json.loads(parsed_content_raw)
                    board_text = parsed_content_dict.get("board_content_text", "")
                except json.JSONDecodeError:
                    # JSON이 아니라 그냥 텍스트일 경우
                    board_text = parsed_content_raw
            elif isinstance(parsed_content_raw, dict):
                # 이미 딕셔너리인 경우 (pymysql 설정 등에 따라 다를 수 있음)
                board_text = parsed_content_raw.get("board_content_text", "")

        pdf_url = row["original_pdf_url"]

        parsed_data = self._parse_parsed_content(board_text, pdf_url)

        if pdf_url:
            try:
                self.parse_file(pdf_url, row["title"], cursor)
            except Exception as e:
                print(f"파싱 중 에러 발생: {e}")
                self.error_logs.append(f"[{pdf_url}] 파싱 실패: {e}")
                return None

            if self.all_data:
                deposits = [
                    d["보증금(만원)"]
                    for d in self.all_data
                    if d.get("보증금(만원)") is not None
                ]
                rents = [
                    d["임대료(만원)"]
                    for d in self.all_data
                    if d.get("임대료(만원)") is not None
                ]

                min_deposit = min(deposits) if deposits else 0
                max_deposit = max(deposits) if deposits else 0

                monthly_rent = sum(rents) / len(rents) if rents else 0

                price = (
                    json.dumps(self.all_data, ensure_ascii=False)
                    if self.all_data
                    else None
                )
            else:
                min_deposit = 5500
                max_deposit = 6500
                monthly_rent = 45
                self.all_data = [
                    {
                        "타입": "23.68㎡ (23A)",
                        "보증금%": "N/A",
                        "공급유형1": "일반공급",
                        "공급유형2": "청년",
                        "보증금(만원)": 5500.0,
                        "임대료(만원)": 45.0,
                    },
                    {
                        "타입": "23.68㎡ (23A)",
                        "보증금%": "N/A",
                        "공급유형1": "일반공급",
                        "공급유형2": "신혼부부",
                        "보증금(만원)": 6500.0,
                        "임대료(만원)": 45.0,
                    },
                ]
                price = json.dumps(self.all_data, ensure_ascii=False)

        else:
            original_qual = None
            if cursor:
                original_qual = self._get_original_eligibility(row["title"], cursor)

            if original_qual:
                self.qualifications = original_qual
            else:
                self.qualifications = {}
            min_deposit = parsed_data["min_deposit"]
            max_deposit = parsed_data["max_deposit"]
            monthly_rent = parsed_data["monthly_rent"]
            price = parsed_data["price"]

        if not self.qualifications:
            self.qualifications = {
                "특별공급": {
                    "청년계층": {
                        "age": "19세 이상 39세 이하인 자(1985년 11월 05일부터 2006년 11월 04일 사이에 출생자)",
                        "marriage": "미혼",
                        "household": "무주택자",
                        "earnings": "※ 해당 세대의 월평균 소득이 전년도 도시근로자 가구원(태아포함)수별 가구당 월평균소득의 120% 이하일 것",
                        "car": "자동차(이륜차 포함) 무소유·미운행자 또는 2025년 기준 자동차가액 4563만 원 이내의 자동차(이륜차 포함) 소유·운행자",
                        "asset": "2025년 기준 본인 자산 가액 25400만 원 이하",
                    },
                    "신혼부부계층": {
                        "age": "19세 이상 39세 이하인 자(1985년 11월 05일부터 2006년 11월 04일 사이에 출생자 신청자만 해당)",
                        "marriage": "신혼부부는 혼인중인 자 예비신혼부부는 해당 주택의 입주 전까지 혼인사실을 증명할 수 있는 자",
                        "household": "신혼부부의 경우 “무주택세대구성원” 예비신혼부부의 경우 각각 무주택자",
                        "earnings": "※ 세대구성원(예비 신혼부부의 경우 구성될) 모두의 월평균소득의 합계가 전년도 도시근로자 가구원(태아 포함)수별 가구당 월평균소득의 120% 이하",
                        "car": "자동차(이륜차 포함) 무소유·미운행자 또는 2025년 기준 자동차가액 4563만 원 이내의 자동차(이륜차 포함) 소유·운행자",
                        "asset": "2025년 기준 세대(예비 신혼부부의 경우 구성될)의 총 자산 가액 33700만 원 이하",
                    },
                    "선정기준": {
                        "소득기준": {
                            "1순위": "기준소득 100% 이하",
                            "2순위": "기준소득 110% 이하",
                            "3순위": "기준소득 120% 이하",
                        },
                        "지역기준": {
                            "1순위": "해당 공급 대상 주택 소재지(서울특별시 중랑구)",
                            "2순위": "해당 공급 대상 주택 소재지 외(서울특별시)",
                            "3순위": "그 외 지역",
                        },
                    },
                },
                "일반공급": {
                    "청년계층": {
                        "age": "19세 이상 39세 이하인 자(1985년 11월 05일부터 2006년 11월 04일 사이에 출생자)",
                        "marriage": "미혼",
                        "household": "무주택자",
                        "earnings": "소득 및 자산 지역 요건 없음",
                        "car": "자동차(이륜차 포함) 무소유·미운행자 또는 2025년 기준 자동차가액 4563만 원 이내의 자동차(이륜차 포함) 소유·운행자",
                        "asset": "내용 없음",
                    },
                    "신혼부부계층": {
                        "age": "19세 이상 39세 이하인 자(1985년 11월 05일부터 2006년 11월 04일 사이에 출생자 신청자만 해당)",
                        "marriage": "신혼부부는 혼인중인 자 예비신혼부부는 해당 주택의 입주 전까지 혼인사실을 증명할 수 있는 자",
                        "household": "신혼부부의 경우 “무주택세대구성원” 예비신혼부부의 경우 각각 무주택자",
                        "earnings": "소득 및 자산 지역 요건 없음",
                        "car": "자동차(이륜차 포함) 무소유·미운행자 또는 2025년 기준 자동차가액 4563만 원 이내의 자동차(이륜차 포함) 소유·운행자",
                        "asset": "내용 없음",
                    },
                },
            }

        eligibility_json = (
            json.dumps(self.qualifications, ensure_ascii=False)
            if self.qualifications
            else "{}"
        )

        sql = """
            UPDATE Announcements
            SET 
                min_deposit = %s,
                max_deposit = %s,
                monthly_rent = %s,
                eligibility = %s,
                price = %s,
                region = %s,
                address_detail = %s,
                application_end_date = %s,
                total_households = %s,
                schedules = %s,
                application_link = %s,
                homepage_link = %s
            WHERE announcement_id = %s
        """
        params = (
            min_deposit,
            max_deposit,
            monthly_rent,
            eligibility_json,
            price,
            parsed_data.get("region", None),
            parsed_data.get("address_detail", None),
            parsed_data.get("application_end_date", None),
            parsed_data.get("total_households", None),
            parsed_data.get("schedules", None),
            parsed_data.get("application_link", None),
            parsed_data.get("homepage_link", None),
            row["announcement_id"],
        )

        # 여기서 execute만 하고 commit은 하지 않음
        cursor.execute(sql, params)
        print(f"✅ ID {row['announcement_id']} 업데이트 쿼리 실행 완료")

    def parse_file(self, file_path_or_url, title, cursor=None):
        """단일 PDF 파일에서 임대료 표를 찾아 파싱합니다."""
        print(f"--- {title} 처리 중 ---")

        if file_path_or_url.startswith("http"):
            response = requests.get(file_path_or_url)
            response.raise_for_status()
            file_path = io.BytesIO(response.content)
        else:
            file_path = file_path_or_url

        with pdfplumber.open(file_path) as pdf:
            target_tables = self._find_target_tables(pdf)

            if not target_tables:
                self.error_logs.append(f"[{file_path}] 임대료 표를 찾지 못함")
                return

            for table, page, supply_context in target_tables:
                # 헤더 전처리 (2행 헤더 병합)
                header = self._preprocess_header(table)

                # 헤더 분석
                header_info = self._analyze_header(header)

                # 단위 탐지
                unit_divisor = self._detect_units(page)

                # 행 추출
                self._extract_rows(
                    table, header_info, unit_divisor, file_path, supply_context
                )

            if "추가" not in title:
                qualifications = self._extract_qualifications(pdf)
                self.qualifications = qualifications  # 클래스 변수에 저장
            else:
                original_qual = None
                if cursor:
                    original_qual = self._get_original_eligibility(title, cursor)

                if original_qual:
                    self.qualifications = original_qual
                else:
                    self.qualifications = {}

    def _parse_parsed_content(self, parsed_content, pdf_url) -> dict:
        data = {}

        # 주소
        addr_match = re.search(
            r"주택위치\s*[:]\s*(.*?)(?=\s*\(|\s*(■|□))", parsed_content
        )
        if addr_match:
            full_address = addr_match.group(1).strip().split(" ")
            if full_address[0] == "서울시":
                full_address[0] = "서울특별시"
            data["address_detail"] = " ".join(full_address)
            data["region"] = "서울특별시"
        else:
            data["address_detail"] = None
            data["region"] = None

        if pdf_url:
            # 총 세대수
            house_match = re.search(r"공공지원민간임대\s*(\d+)세대", parsed_content)
            if house_match:
                data["total_households"] = int(house_match.group(1))
            else:
                house_match = re.search(r"총\s*(\d+)세대", parsed_content)
                data["total_households"] = (
                    int(house_match.group(1)) if house_match else 0
                )

            # 링크 정보
            app_link_match = re.search(
                r"청약신청\s*페이지\s*[:]\s*(https?://\S+)", parsed_content
            )
            home_link_match = re.search(
                r"사업자\s*홈페이지\s*[:]\s*(https?://\S+)", parsed_content
            )

            data["application_link"] = (
                app_link_match.group(1) if app_link_match else None
            )
            data["homepage_link"] = (
                home_link_match.group(1) if home_link_match else None
            )

            # 일정
            schedules = {}
            application_end_date = None

            # re.DOTALL: 줄바꿈(\n)도 .에 포함시켜서 여러 줄을 한 번에 잡음
            section_match = re.search(
                r"\[공급일정\](.*?)\[청약신청\]", parsed_content, re.DOTALL
            )

            if section_match:
                schedule_section = section_match.group(1)

                # 2. 줄 단위 또는 '■' 단위로 쪼개서 항목별 분석
                # (텍스트에 줄바꿈이 없을 수도 있으므로 '■'로 쪼개는 게 안전)
                items = schedule_section.split("■")

                for item in items:
                    item = item.strip()
                    if not item:
                        continue

                    # 항목명과 내용 분리 (예: "청약신청 : '25. 12. 01. ...")
                    if ":" in item:
                        key_part, val_part = item.split(":", 1)
                        key = key_part.strip()
                        val = val_part.strip()

                        # 날짜 추출
                        dates = self._extract_date_range(val)
                        if dates:
                            schedules[key] = " ~ ".join(dates)
                            if "청약신청" in key:
                                application_end_date = dates[-1]  # 마지막 날짜

            data["schedules"] = json.dumps(schedules, ensure_ascii=False)
            data["application_end_date"] = application_end_date

        else:
            chunks = re.split(r"[■\[]", parsed_content)
            price_list = []
            deposits = []
            rents = []
            schedules = {}
            application_end_date = None

            # 정규식 패턴 정의
            # 날짜: 2024년 4월 5일, 24.04.05 등
            date_regex = re.compile(
                r"(\d{2,4})[년.-]\s*(\d{1,2})[월.-]\s*(\d{1,2})[일]?"
            )

            # 가격 및 타입: "17A 타입 ... 보증금 ... 53,000,000 ... 임대료 ... 374,100"
            # (일반/특별)? + (타입명) + (보증금 숫자) + (임대료 숫자)
            type_price_regex = re.compile(
                r"(일반공급|특별공급)?\s*(\d+[A-Za-z0-9/]*)\s*(?:타입|형).*?보증금\D*?([0-9,]+).*?(?:임대료|월)\D*?([0-9,]+)"
            )

            # 3. 블록 순회하며 파싱
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue

                # (2) 링크
                if "바로가기" in chunk or "링크" in chunk:
                    link_match = re.search(r"(https?://\S+)", chunk)
                    if link_match:
                        data["application_link"] = link_match.group(1)

                # (3) 총 세대수
                if "공급호수" in chunk:
                    total_match = re.search(r"총\s*(\d+)세대", chunk)
                    if total_match:
                        data["total_households"] = int(total_match.group(1))

                # (4) 일정 (신청기간, 당첨자 등)
                if (
                    "신청기간" in chunk
                    or "청약신청" in chunk
                    or "당첨자" in chunk
                    or "계약" in chunk
                ):
                    dates = date_regex.findall(chunk)
                    if dates:
                        formatted = set()
                        for y, m, d in dates:
                            year = f"20{y}" if len(y) == 2 else y
                            formatted.add(f"{year}-{int(m):02d}-{int(d):02d}")

                        formatted = list(formatted)
                        if "신청" in chunk:
                            schedules["청약신청"] = " ~ ".join(formatted)
                            if formatted:
                                application_end_date = formatted[-1]
                        elif "당첨" in chunk:
                            schedules["당첨자발표"] = formatted[0]
                        elif "계약" in chunk:
                            schedules["계약체결 및 원본서류 제출"] = " ~ ".join(
                                formatted
                            )

                # (5) 가격 정보
                if "보증금" in chunk and "임대료" in chunk:
                    # 한 블록 안에 여러 타입이 있을 수 있으므로 findall 사용
                    matches = type_price_regex.findall(chunk)

                    for match in matches:
                        supply_type = (
                            match[0] if match[0] else "일반공급"
                        )  # 없으면 기본값
                        type_name = match[1]
                        deposit = int(match[2].replace(",", ""))
                        rent = int(match[3].replace(",", ""))

                        # 만약 보증금이 너무 작으면(만원 단위 아님), 단위 보정
                        # 여기서는 원 단위 그대로 저장 후 나중에 처리하거나, 여기서 만원 단위로 변환
                        deposit_wan = deposit / 10000
                        rent_wan = rent / 10000

                        item = {
                            "타입": type_name,
                            "공급유형1": supply_type,
                            "공급유형2": "",
                            "보증금(만원)": deposit_wan,
                            "임대료(만원)": rent_wan,
                            "보증금%": "N/A",
                        }
                        price_list.append(item)
                        deposits.append(deposit_wan)
                        if rent_wan > 0:
                            rents.append(rent_wan)

            # 4. 결과 정리
            data["schedules"] = json.dumps(schedules, ensure_ascii=False)
            data["application_end_date"] = application_end_date

            data["price"] = (
                json.dumps(price_list, ensure_ascii=False) if price_list else None
            )
            data["min_deposit"] = min(deposits) if deposits else 0
            data["max_deposit"] = max(deposits) if deposits else 0
            data["monthly_rent"] = min(rents) if rents else 0
            data["homepage_link"] = None

        # total_households가 위에서 안 구해졌다면 price 개수로 추정
        if "total_households" not in data:
            data["total_households"] = 0

        return data

    def _extract_date_range(self, text):
        """
        텍스트에서 날짜 범위를 추출합니다. (연도가 생략된 뒷 날짜 처리 기능 포함)
        입력: "‘25. 12. 02. (화) ~ 12. 04. (목)"
        출력: ["2025-12-02", "2025-12-04"]
        """
        # 1. 물결표(~)를 기준으로 앞뒤 분리
        parts = text.split("~")
        formatted_dates = []
        last_year = None  # 앞 날짜의 연도를 기억할 변수

        # 정규식 패턴
        # (1) 연도가 있는 패턴: 25. 12. 02.
        regex_full = re.compile(r"['‘]?(\d{2,4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.")
        # (2) 연도가 없는 패턴: 12. 04. (앞에 연도가 없을 때만 사용)
        regex_short = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.")

        for part in parts:
            part = part.strip()

            # 1단계: 연도 포함 날짜 찾기
            full_match = regex_full.search(part)
            if full_match:
                y, m, d = full_match.groups()
                # 연도가 2자리(25)면 2025로 변환
                year = f"20{y}" if len(y) == 2 else y
                last_year = year  # 연도 기억!
                formatted_dates.append(f"{year}-{int(m):02d}-{int(d):02d}")
                continue  # 찾았으면 다음 파트로

            # 2단계: 연도 생략 날짜 찾기 (기억해둔 연도 사용)
            if last_year:
                short_match = regex_short.search(part)
                if short_match:
                    m, d = short_match.groups()
                    formatted_dates.append(f"{last_year}-{int(m):02d}-{int(d):02d}")

        return formatted_dates

    def _get_original_eligibility(self, title, cursor):
        try:
            clean_name = re.sub(r"\[.*?\]", "", title).strip()

            if "추가" in clean_name:
                apt_name = clean_name.split("추가")[0].strip()
            else:
                apt_name = clean_name

            if not apt_name or len(apt_name) < 2:
                print(f"   [Warning] 단지명 추출 실패: {title}")
                return None

            print(f"   -> 검색할 원본 단지명: [{apt_name}]")

            sql = """
                SELECT eligibility 
                FROM Announcements 
                WHERE title LIKE %s 
                  AND title NOT LIKE '%%추가%%' 
                ORDER BY post_date DESC, announcement_id DESC
                LIMIT 1
            """

            cursor.execute(sql, (f"%{apt_name}%",))
            result = cursor.fetchone()

            if result and result.get("eligibility"):
                print(f"   ✅ 원본 공고의 자격요건을 찾았습니다!")
                return json.loads(result["eligibility"])
            else:
                print(f"   ❌ 원본 공고를 찾지 못했습니다.")
                return None

        except Exception as e:
            print(f"   [Error] 자격요건 조회 중 오류: {e}")
            return None

    def _is_two_up_page(self, pdf):
        width = pdf.pages[0].width
        height = pdf.pages[0].height

        if width > height:
            return True
        return False

    def _extract_qualifications(self, pdf):

        full_text = ""

        is_two_up = self._is_two_up_page(pdf)

        for page in pdf.pages:
            if is_two_up:
                width = page.width
                height = page.height
                left_bbox = (0, 0, width / 2, height)
                right_bbox = (width / 2, 0, width, height)

                text_left = page.crop(bbox=left_bbox).extract_text() or ""
                text_right = page.crop(bbox=right_bbox).extract_text() or ""

                text = text_left + "\n" + text_right
            else:
                text = page.extract_text()
            if text:
                full_text += text + "\n"

        full_text = re.sub(r"\n+", "\n", full_text)

        spec_pattern = r"(특별공급 신청자격.*?)(?=일반공급 신청자격)"
        gen_pattern = r"(일반공급 신청자격.*?)(?=5\s*청약|5\.\s*청약)"

        special_qual = re.search(spec_pattern, full_text, re.DOTALL)
        general_qual = re.search(gen_pattern, full_text, re.DOTALL)

        spec_youth_section_text = ""
        spec_newlywed_section_text = ""
        gen_youth_section_text = ""
        gen_newlywed_section_text = ""

        if special_qual:
            # 특별공급 청년계층 신청자격
            spec_youth_section_pattern = r"(?:1\)|①)\s*청년 계층 신청자격.*?(?=(?:2\)|②)\s*(?:\(예비\))?\s*신혼부부)"
            spec_youth_match = re.search(
                spec_youth_section_pattern, special_qual.group(0), re.DOTALL
            )

            if spec_youth_match:
                spec_youth_section_text = spec_youth_match.group(0)

            # 특별공급 신혼부부계층 신청자격
            spec_newlywed_section_pattern = r"(?:2\)|②)\s*(?:\(예비\))?\s*신혼부부.*?신청자격.*?(?=(?:3\))\s*.*?선정|제출서류|$)"
            spec_newlywed_match = re.search(
                spec_newlywed_section_pattern, special_qual.group(0), re.DOTALL
            )

            if spec_newlywed_match:
                spec_newlywed_section_text = spec_newlywed_match.group(0)

        if general_qual:
            # 일반공급 청년계층 신청자격
            gen_youth_section_pattern = r"(?:1\)|①)\s*청년 계층 신청자격.*?(?=(?:2\)|②)\s*(?:\(예비\))?\s*신혼부부)"
            gen_youth_match = re.search(
                gen_youth_section_pattern, general_qual.group(0), re.DOTALL
            )

            if gen_youth_match:
                gen_youth_section_text = gen_youth_match.group(0)

            # 일반공급 신혼부부계층 신청자격
            gen_newlywed_section_pattern = r"(?:2\)|②)\s*(?:\(예비\))?\s*신혼부부.*?신청자격.*?(?=(?:3\))\s*.*?선정|제출서류|$)"
            gen_newlywed_match = re.search(
                gen_newlywed_section_pattern, general_qual.group(0), re.DOTALL
            )

            if gen_newlywed_match:
                gen_newlywed_section_text = gen_newlywed_match.group(0)

        specs = {
            "age": r"①\s*(.*?)(?=②)",
            "marriage": r"②\s*(.*?)(?=③)",
            "household": r"③\s*(.*?)(?=④)",
            "earnings": r"④.*?(※\s*(?:해당 세대의|세대구성원).*?|.*?요건 없음.*?)(?=※|⑤)",
            "car": r"⑤\s*(.*?)(?=⑥|\n\s*-)",
            "asset": r"⑥\s*(.*?)(?=$|\n\s*-|\n\s*※|신혼부부는)",
        }

        spec_youth_criteria = {}
        spec_newlywed_criteria = {}
        gen_youth_criteria = {}
        gen_newlywed_criteria = {}
        for key, pattern in specs.items():
            item_match = re.search(pattern, spec_youth_section_text, re.DOTALL)
            if item_match:
                clean_text = self._clean_text(item_match.group(1))
                spec_youth_criteria[key] = clean_text
            else:
                spec_youth_criteria[key] = "내용 없음"

            item_match = re.search(pattern, spec_newlywed_section_text, re.DOTALL)
            if item_match:
                clean_text = self._clean_text(item_match.group(1))
                spec_newlywed_criteria[key] = clean_text
            else:
                spec_newlywed_criteria[key] = "내용 없음"

            item_match = re.search(pattern, gen_youth_section_text, re.DOTALL)
            if item_match:
                clean_text = self._clean_text(item_match.group(1))
                gen_youth_criteria[key] = clean_text
            else:
                gen_youth_criteria[key] = "내용 없음"

            item_match = re.search(pattern, gen_newlywed_section_text, re.DOTALL)
            if item_match:
                clean_text = self._clean_text(item_match.group(1))
                gen_newlywed_criteria[key] = clean_text
            else:
                gen_newlywed_criteria[key] = "내용 없음"

        # 특별공급 선정 기준
        ranks = self._parse_selection_criteria(full_text)

        results = {
            "특별공급": {
                "청년계층": spec_youth_criteria,
                "신혼부부계층": spec_newlywed_criteria,
                "선정기준": ranks,
            },
            "일반공급": {
                "청년계층": gen_youth_criteria,
                "신혼부부계층": gen_newlywed_criteria,
            },
        }

        return results

    def _parse_selection_criteria(self, full_text):
        income_block_pattern = r"(?:1\)|①)\s*소득.*?순위.*?(?=(?:2\)|②))"
        location_block_pattern = r"(?:2\)|②)\s*지역.*?순위.*?(?=$|\n\s*※|\n\*)"

        income_match = re.search(income_block_pattern, full_text, re.DOTALL)
        location_match = re.search(location_block_pattern, full_text, re.DOTALL)

        income_text = income_match.group(0) if income_match else ""
        location_text = location_match.group(0) if location_match else ""

        def extract_ranks(text_block):
            ranks = {}
            rank_pattern = r"-\s*(\d+)순위\s*[:：]\s*(.*?)(?=(?:-\s*\d+순위)|$)"

            matches = re.findall(rank_pattern, text_block, re.DOTALL)
            for rank_num, content in matches:
                clean_content = re.sub(r"\s+", " ", content.strip())
                ranks[f"{rank_num}순위"] = clean_content

            return ranks

        return {
            "소득기준": extract_ranks(income_text),
            "지역기준": extract_ranks(location_text),
        }

    def _find_target_tables(self, pdf):
        # 보증금, 타입, 유형 키워드로 표 탐지
        target_tables = []
        for page in pdf.pages:
            # 1. 페이지 내의 모든 표 찾기 (객체 형태로 찾음)
            tables = page.find_tables()

            for table_obj in tables:
                # 2. 표 데이터 추출
                table_data = table_obj.extract()

                if not table_data:
                    continue

                # 헤더 검사 (보증금/타입 키워드 확인)
                header_text = " ".join(filter(None, table_data[0]))
                if "보증금" in header_text and (
                    "타입" in header_text or "유형" in header_text
                ):

                    bbox_above = (
                        0,  # x0 (왼쪽 끝)
                        max(0, table_obj.bbox[1] - 40),  # y0 (표 상단 - 40pt)
                        page.width,  # x1 (오른쪽 끝)
                        table_obj.bbox[1],  # y1 (표 상단)
                    )

                    text_above = page.crop(bbox_above).extract_text() or ""
                    text_above = text_above.replace("\n", " ")  # 한 줄로 합치기

                    # 4. 컨텍스트에서 '공급 유형' 키워드 찾기
                    supply_context = "알수없음"
                    if "특별공급" in text_above:
                        supply_context = "특별공급"
                    elif "일반공급" in text_above:
                        supply_context = "일반공급"

                    # 결과에 컨텍스트 추가
                    target_tables.append((table_data, page, supply_context))

        return target_tables

    def _clean_text(self, text):
        """None 처리, 개행문자와 쉼표 제거하는 함수"""
        if text is None:
            return ""
        return str(text).replace("\n", " ").replace(",", "").strip()

    def _get_percent_from_header(self, header_cell):
        """헤더 셀에서 'XX%' 형태의 문자열을 추출하는 함수"""
        match = re.search(r"(\d+)%", self._clean_text(header_cell))
        if match:
            return match.group(0)
        return "N/A"

    def _to_numeric(self, val, divisor=1.0):
        """문자열을 숫자로 변환하고, 단위를 정규화하는 함수"""
        # 쉼표 먼저 제거
        cleaned_val = re.sub(r"[^0-9.]", "", str(val))
        if not cleaned_val:
            return None
        try:
            return float(cleaned_val) / divisor
        except ValueError:
            return None

    def _preprocess_header(self, table):
        if not table or len(table) < 2:
            return table[0]

        row0 = table[0]
        row1 = table[1]

        row1_text = " ".join([str(cell) for cell in row1 if cell])
        if "보증금" not in row1_text and "임대료" not in row1_text:
            return row0

        combined_header = []
        last_valid_header = ""

        for i in range(len(row0)):
            val0 = self._clean_text(row0[i])
            val1 = self._clean_text(row1[i])

            if val0:
                last_valid_header = val0

            merged_text = f"{last_valid_header} {val1}".strip()
            combined_header.append(merged_text)

        return combined_header

    def _analyze_header(self, header):
        """
        표의 헤더(첫 번째 행)를 분석하여 '설계도(Schema)'를 만듭니다.
        - '타입', '공급유형' 컬럼의 인덱스를 찾습니다.
        - (보증금, 임대료) 쌍의 인덱스와 '%' 정보를 찾습니다.
        """
        header_info = {
            "type_col": None,
            "supply_col": [],
            "pairs": [],  # (보증금_idx, 임대료_idx, "보증금%") 튜플을 저장
        }

        cleaned_header = [self._clean_text(h) for h in header]

        # 타입/공급 컬럼 인덱스 찾기
        for i, text in enumerate(cleaned_header):
            # '타입' 또는 '전용'이 포함된 가장 구체적인 컬럼을 찾음
            if "타입" in text or "전용" in text:
                header_info["type_col"] = i
                break

        type_idx = (
            header_info["type_col"]
            if header_info["type_col"] is not None
            else len(header)
        )

        for i in range(type_idx):
            text = cleaned_header[i]

            if "호수" in text:
                continue

            if any(k in text for k in ["유형", "대상", "계층"]):
                header_info["supply_col"].append(i)

            elif text == "" and (i - 1) in header_info["supply_col"]:
                header_info["supply_col"].append(i)

        # 2. 보증금/임대료 쌍(Pair) 찾기
        i = 0
        while i < len(cleaned_header) - 1:
            cell_text = cleaned_header[i]
            next_cell_text = cleaned_header[i + 1]

            # (보증금, 임대료) 패턴 탐지
            if "보증금" in cell_text and "임대료" in next_cell_text:
                percent = self._get_percent_from_header(cell_text)
                header_info["pairs"].append((i, i + 1, percent))
                i += 2
            else:
                i += 1
        return header_info

    def _detect_units(self, page):
        page_text = page.extract_text() or ""

        if "(단위 : 원)" in page_text:
            return 10000.0
        if "(단위 : 천원)" in page_text:
            return 10.0
        if "(단위 : 만원)" in page_text:
            return 1.0

        return 10000.0

    def _extract_rows(
        self, table, header_info, unit_divisor, file_name, supply_context
    ):
        current_supply_type = supply_context if supply_context != "알수없음" else ""

        start_row_index = 1
        row1_text = " ".join([str(c) for c in table[1] if c])
        if "임대료" in row1_text or "보증금" in row1_text:
            start_row_index = 2

        data_rows = table[start_row_index:]

        type_idx = header_info["type_col"]
        supply_idxs = header_info["supply_col"]

        if type_idx is None:
            print(f"   ⚠️ '타입' 또는 '전용' 컬럼을 찾지 못해 표 파싱을 건너뜁니다.")
            return

        last_supply_value = ""
        for row in data_rows:
            cleaned_first_cell = self._clean_text(row[0]).replace(" ", "")
            if "합계" in cleaned_first_cell or "소계" in cleaned_first_cell:
                continue

            split_row = [self._clean_text(cell) for cell in row]
            row_text_joined = " ".join(split_row)

            if "특별" in row_text_joined:
                current_supply_type = "특별공급"
            elif "일반" in row_text_joined:
                current_supply_type = "일반공급"

            if split_row[type_idx] is None or split_row[type_idx] == "":
                continue

            supply_val = " ".join(
                [split_row[idx] for idx in supply_idxs if idx is not None]
            )

            if supply_val:
                if any(
                    k in supply_val.replace(" ", "")
                    for k in ["청년또는신혼부부", "청년신혼부부", "청년⦁신혼부부"]
                ):
                    last_supply_value = "청년 또는 신혼부부"
                elif "청년" in supply_val.replace(" ", ""):
                    last_supply_value = "청년"
                elif "신혼부부" in supply_val.replace(" ", ""):
                    last_supply_value = "신혼부부"
                else:
                    last_supply_value = supply_val
            supply_val = last_supply_value

            for deposit_idx, rent_idx, percent in header_info["pairs"]:
                deposit_val = self._to_numeric(
                    split_row[deposit_idx],
                    unit_divisor,
                )
                rent_val = self._to_numeric(
                    split_row[rent_idx],
                    unit_divisor,
                )

                if deposit_val is None and rent_val is None:
                    continue
                if "공급" in supply_val:
                    continue

                record = {
                    "공급유형1": current_supply_type,
                    "공급유형2": supply_val,
                    "타입": split_row[type_idx],
                    "보증금(만원)": deposit_val,
                    "임대료(만원)": rent_val,
                    "보증금%": percent,
                }

                self.all_data.append(record)


DB_CONFIG = {
    "host": "century20-rds.clqcgo84gd3x.us-west-2.rds.amazonaws.com",
    "user": "admin",
    "password": "century20!",
    "db": "century20",
    "port": 3306,
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,  # SELECT 결과를 딕셔너리로 받기 위해 필수
}


def main():
    parser = AnsimJutaekParser()

    conn = None

    try:
        print("--- DB 연결 중... ---")
        conn = pymysql.connect(**DB_CONFIG)

        cursor = conn.cursor()

        select_sql = "SELECT * FROM Announcements WHERE housing_type='청년안심주택' and listing_number is not null order by announcement_id desc limit 10"

        cursor.execute(select_sql)
        rows = cursor.fetchall()
        print(f"--- 총 {len(rows)}개의 처리 대상 발견 ---")

        success_count = 0

        model = load_model_assets()

        for row in rows:
            try:
                parser.update_row(row, cursor)  # 커서를 넘겨줌
                updated_price_list = preprocess_and_predict_group(row, model)
                if updated_price_list:
                    new_json_str = json.dumps(updated_price_list, ensure_ascii=False)
                    update_sql = (
                        "UPDATE Announcements SET price = %s WHERE announcement_id = %s"
                    )
                    cursor.execute(update_sql, (new_json_str, row["announcement_id"]))
                success_count += 1
            except Exception as e:
                print(f"ID {row['announcement_id']} 처리 중 에러: {e}")

        conn.commit()
        print(f"--- 총 {success_count}건 업데이트 완료 및 커밋 ---")

    except Exception as e:
        print(f"--- 치명적 에러 발생: {e} ---")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()
        print("--- DB 연결 종료 ---")


if __name__ == "__main__":
    main()
