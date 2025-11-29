# test_playwright.py
from playwright.sync_api import sync_playwright
import requests, sys, time, traceback

FORM_URL = "https://naver.me/FW092IDY"

def resolve_url(url: str) -> str:
    r = requests.get(url, allow_redirects=True, timeout=10)
    r.raise_for_status()
    return r.url

def main():
    print("[START]")
    try:
        final_url = resolve_url(FORM_URL)
        print(f"[INFO] Resolved: {final_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(final_url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            ok = False
            try:
                page.locator('[role="radiogroup"]').first.get_by_role("radio").nth(1).check()
                ok = True
                print("[OK] via radiogroup")
            except Exception:
                pass

            if not ok:
                try:
                    page.get_by_role("group").first.get_by_role("radio").nth(1).check()
                    ok = True
                    print("[OK] via group")
                except Exception:
                    pass

            if not ok:
                radios = page.locator('input[type="radio"]')
                cnt = radios.count()
                print(f"[DEBUG] radio count={cnt}")
                if cnt >= 2:
                    radios.nth(1).check(force=True)
                    ok = True
                    print("[OK] via input[type=radio] nth(2)")

            if not ok:
                labels = page.locator("label")
                cnt = labels.count()
                print(f"[DEBUG] label count={cnt}")
                if cnt >= 2:
                    labels.nth(1).click(force=True)
                    ok = True
                    print("[OK] via label nth(2)")

            page.screenshot(path="after_select.png", full_page=True)
            print(f"[DONE] Selected second option: {ok}. Screenshot: after_select.png")
            time.sleep(1)
            browser.close()
    except Exception as e:
        print("[ERROR]", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()