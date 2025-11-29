from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

import requests
from playwright.sync_api import Page, sync_playwright


def resolve_url(url: str) -> str:
    resp = requests.get(url, allow_redirects=True, timeout=15)
    resp.raise_for_status()
    return resp.url


def try_select_option_in_group(
    page: Page, group: Page, option_index_zero_based: int
) -> bool:
    # 우선 접근성 role 기반
    try:
        radios = group.get_by_role("radio")
        if radios.count() > option_index_zero_based:
            radios.nth(option_index_zero_based).check()
            return True
    except Exception:
        pass

    # input[type=radio] 기반
    try:
        radios = group.locator('input[type="radio"]')
        if radios.count() > option_index_zero_based:
            radios.nth(option_index_zero_based).check(force=True)
            return True
    except Exception:
        pass

    # 라벨 클릭(보편적 Fallback)
    try:
        labels = group.locator("label")
        if labels.count() > option_index_zero_based:
            labels.nth(option_index_zero_based).click(force=True)
            return True
    except Exception:
        pass

    return False


def select_choice(
    page: Page, question_index_zero_based: int, option_index_zero_based: int
) -> None:
    # 1) radiogroup
    rg = page.locator('[role="radiogroup"]')
    if rg.count() > question_index_zero_based:
        group = rg.nth(question_index_zero_based)
        if try_select_option_in_group(page, group, option_index_zero_based):
            return

    # 2) 일반 group
    grp = page.get_by_role("group")
    if grp.count() > question_index_zero_based:
        group = grp.nth(question_index_zero_based)
        if try_select_option_in_group(page, group, option_index_zero_based):
            return

    # 3) 페이지 전체 fallback
    #    첫 번째 질문의 두 번째 라디오를 강제로 선택
    radios = page.locator('input[type="radio"]')
    if radios.count() >= option_index_zero_based + 1:
        radios.nth(option_index_zero_based).check(force=True)
        return

    raise RuntimeError("선택지 선택 실패: 셀렉터 조정이 필요합니다.")


def click_submit(page: Page) -> bool:
    # 버튼 텍스트 후보
    names = [
        "제출",
        "보내기",
        "제출하기",
        "등록",
        "확인",
        "Next",
        "Submit",
        "Send",
        "다음",
    ]
    for name in names:
        try:
            page.get_by_role("button", name=name).click(timeout=1500)
            return True
        except Exception:
            continue
    return False


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Naver Form 자동 선택/제출 (헤드리스)")
    parser.add_argument("--url", required=True, help="네이버 폼 URL(단축 주소 가능)")
    parser.add_argument(
        "--question",
        type=int,
        default=1,
        help="질문 번호(1부터). 기본: 1",
    )
    parser.add_argument(
        "--choice",
        type=int,
        default=2,
        help="선택지 번호(1부터). 기본: 2",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="선택 후 제출까지 수행",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="창 보이기(디버그용). 기본은 헤드리스",
    )
    args = parser.parse_args(argv)

    q_idx = max(1, args.question) - 1
    c_idx = max(1, args.choice) - 1

    final_url = resolve_url(args.url)
    print(f"[INFO] Resolved URL: {final_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful)
        page = browser.new_page()
        page.goto(final_url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        time.sleep(0.8)

        select_choice(page, q_idx, c_idx)
        print(f"[OK] 선택 완료: question={args.question}, choice={args.choice}")

        if args.submit:
            if click_submit(page):
                print("[OK] 제출 버튼 클릭 완료")
            else:
                print("[WARN] 제출 버튼을 찾지 못했습니다. 수동 확인 필요")

        # 증빙용 스크린샷(헤드리스에서도 저장)
        page.screenshot(path="naver_form_after.png", full_page=True)
        print("[INFO] Saved: naver_form_after.png")

        time.sleep(0.5)
        browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

