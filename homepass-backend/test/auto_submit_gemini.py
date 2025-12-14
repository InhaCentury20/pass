import time
from playwright.sync_api import sync_playwright

# ============================================================
# ⚙️ [설정]
# ============================================================
TARGET_FORM_URL = "https://form.naver.com/response/9YZljQp2eaxRn5IxDnbDJQ"
DO_ACTUAL_SUBMIT = True

# ============================================================
# 👥 [사용자 데이터]
# ============================================================
USERS = [
    {
        "name": "김철수",
        "phone": "010-1111-1111",
        "birthdate": "20000729",  # 요청하신 대로 8자리 숫자 텍스트
        "address_keyword": "통일로 838-21",
        "address_detail": "101호",
        "email": "kim@test.com",
        "type": "청년 일반공급 17.05", # 텍스트 일부만 맞아도 됨
        "income": "1",  # "1" 또는 "1순위" 등 텍스트
        "region": "1",
        "asset": "해당없음",
        "house": "미소유",
    }
]

def force_react_change(page, selector, value):
    """
    [핵심 함수] React/Vue가 input 값 변경을 인지하도록 강제 이벤트를 발생시킴
    이게 없으면 상세주소나 생년월일이 입력된 것 같아도 제출하면 비어있음으로 뜸.
    """
    page.evaluate(f"""
        () => {{
            const el = document.querySelector('{selector}');
            if (el) {{
                // 1. 값 설정 (React Hook 우회)
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, "value"
                ).set;
                
                // textarea인 경우 처리
                if (el.tagName.toLowerCase() === 'textarea') {{
                     const nativeTextAreaSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLTextAreaElement.prototype, "value"
                    ).set;
                    nativeTextAreaSetter.call(el, '{value}');
                }} else {{
                    nativeInputValueSetter.call(el, '{value}');
                }}

                // 2. 이벤트 강제 발생
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        }}
    """)

def run_automation():
    with sync_playwright() as p:
        # 브라우저 실행 (속도 조절 slow_mo=100)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        page.set_default_timeout(20000)

        try:
            for idx, user in enumerate(USERS, 1):
                print(f"\n{'='*60}")
                print(f"▶ [{idx}/{len(USERS)}] 사용자 '{user['name']}' 시작")
                print(f"{'='*60}\n")

                print(f"🌐 접속 중: {TARGET_FORM_URL}")
                page.goto(TARGET_FORM_URL, wait_until='networkidle')

                if "nid.naver.com" in page.url:
                    print("🔐 로그인 필요 (60초 대기)")
                    page.wait_for_url("**/form.naver.com/response/**", timeout=60000)
                    print("✅ 로그인 완료")
                
                page.wait_for_selector('div[role="group"]', state='visible')
                print("📝 데이터 입력 시작\n")

                # =========================================================
                # 1. 이름 & 2. 연락처 (단순 입력)
                # =========================================================
                try:
                    print(f"1️⃣ 이름: {user['name']}")
                    page.locator('div[role="group"][aria-label*="이름"] input').fill(user['name'])
                    
                    print(f"2️⃣ 연락처: {user['phone']}")
                    page.locator('div[role="group"][aria-label*="연락처"] input').fill(user['phone'].replace('-', ''))
                except Exception as e:
                    print(f"   ❌ 기본정보 입력 실패: {e}")

                # =========================================================
                # 3. 생년월일 (Textarea - 20000729 텍스트 입력)
                # =========================================================
                print(f"3️⃣ 생년월일: {user['birthdate']}")
                try:
                    birth_section = page.locator('div[role="group"][aria-label*="생년월일"]')
                    # HTML 구조상 textarea임
                    textarea = birth_section.locator('textarea')
                    
                    if textarea.count() > 0:
                        textarea.click()
                        # 단순 fill이 안 먹힐 때를 대비해 강제 주입 함수 사용
                        force_react_change(page, 'div[role="group"][aria-label*="생년월일"] textarea', user['birthdate'])
                        print("   ✅ 입력 완료")
                    else:
                        print("   ❌ 생년월일 입력창(textarea)을 찾을 수 없음")
                except Exception as e:
                    print(f"   ❌ 실패: {e}")

                # =========================================================
                # 4. 주소 (모달 검색 + 상세주소 강제 주입)
                # =========================================================
                print(f"4️⃣ 주소: {user['address_keyword']}")
                try:
                    addr_group = page.locator('div[role="group"][aria-label*="주소"]')
                    
                    # 검색 버튼 클릭
                    addr_group.locator('button', has_text='주소검색').click()
                    
                    # 모달 대기
                    modal = page.locator('.nsv_layer_postcode')
                    modal.wait_for(state='visible', timeout=5000)
                    
                    # 검색 및 결과 클릭
                    modal.locator('input.nsv_layer_postcode_search_input').fill(user['address_keyword'])
                    modal.locator('button.nsv_layer_button_postcode_search').click()
                    time.sleep(1)  # 검색 결과 대기
                    
                    result_btn = modal.locator('ul.nsv_layer_address_list li button').first
                    result_btn.wait_for(state='visible', timeout=5000)
                    result_btn.click()
                    
                    # [중요] 모달 닫히고 본문 반영 대기
                    print("   ⏳ 주소 반영 대기...")
                    modal.wait_for(state='hidden', timeout=10000)
                    time.sleep(1.5)  # 추가 안정화 대기

                    # 상세주소 입력 - 다양한 방법 시도
                    print("   📝 상세주소 입력 시도...")
                    
                    # 방법 1: placeholder로 찾기
                    detail_inputs = addr_group.locator('input[placeholder*="상세"]')
                    if detail_inputs.count() > 0:
                        detail_input = detail_inputs.last  # 마지막 input (상세주소)
                        detail_input.scroll_into_view_if_needed()
                        detail_input.click()
                        time.sleep(0.3)
                        
                        # 직접 evaluate로 값 설정
                        detail_input.evaluate(f"""
                            (el) => {{
                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                                    window.HTMLInputElement.prototype, "value"
                                ).set;
                                nativeInputValueSetter.call(el, '{user['address_detail']}');
                                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            }}
                        """)
                        time.sleep(0.3)
                        
                        # 검증
                        actual_value = detail_input.input_value()
                        if actual_value == user['address_detail']:
                            print(f"   ✅ 상세주소 입력 완료: {user['address_detail']}")
                        else:
                            print(f"   ⚠️ 입력값 불일치: 예상='{user['address_detail']}', 실제='{actual_value}'")
                            # 재시도: fill 방식
                            detail_input.fill(user['address_detail'])
                            time.sleep(0.5)
                            print(f"   ✅ 재시도로 입력 완료")
                    else:
                        print("   ❌ 상세주소 입력창을 찾을 수 없음")
                    
                except Exception as e:
                    print(f"   ❌ 주소 실패: {e}")
                    import traceback
                    traceback.print_exc()
                    # 모달 닫기 시도
                    try:
                        if page.locator('.nsv_layer_button_close').is_visible():
                            page.locator('.nsv_layer_button_close').click()
                    except:
                        pass

                # =========================================================
                # 5. 이메일
                # =========================================================
                try:
                    print(f"5️⃣ 이메일: {user['email']}")
                    page.locator('div[role="group"][aria-label*="이메일"] input').fill(user['email'])
                except: pass

                # =========================================================
                # 6~11. 선택형 항목 (개선된 로직 - 중복 클릭 방지)
                # =========================================================
                def smart_select(label_keyword, option_keyword, step_num):
                    print(f"{step_num} {label_keyword}: {option_keyword}")
                    try:
                        # 1. 섹션(질문) 찾기
                        section = page.locator(f'div[role="group"][aria-label*="{label_keyword}"]')
                        section.scroll_into_view_if_needed()
                        time.sleep(0.2)
                        
                        # 2. 라벨 찾기 (텍스트 포함)
                        target_label = section.locator('label').filter(has_text=option_keyword).first
                        
                        # 3. 만약 텍스트로 못 찾았는데 옵션이 숫자("1")라면 정확한 매칭 시도
                        if target_label.count() == 0 and option_keyword.isdigit():
                            # 정확히 "1", "2" 같은 텍스트를 가진 라벨 찾기
                            all_labels = section.locator('label').all()
                            for lbl in all_labels:
                                text = lbl.inner_text().strip()
                                if text == option_keyword or text.startswith(f"{option_keyword}순위") or text.startswith(f"{option_keyword}."):
                                    target_label = lbl
                                    break

                        # 4. 클릭 전 상태 확인
                        if target_label.count() == 0:
                            print(f"   ❌ 옵션 라벨을 찾을 수 없음: {option_keyword}")
                            all_labels = section.locator('label').all_inner_texts()
                            print(f"      (가능한 옵션: {all_labels})")
                            return
                        
                        # 5. 이미 선택되어 있는지 확인
                        input_el = target_label.locator('input')
                        if input_el.count() > 0:
                            is_checked = input_el.is_checked()
                            if is_checked:
                                print("   ℹ️ 이미 선택되어 있음")
                                return
                        
                        # 6. 한 번만 클릭
                        target_label.click(force=True)
                        time.sleep(0.4)  # 클릭 반영 대기
                        
                        # 7. 선택 결과 확인
                        if input_el.count() > 0:
                            is_checked = input_el.is_checked()
                            if is_checked:
                                print("   ✅ 선택 성공")
                                return
                        
                        # aria-checked로도 확인
                        aria_checked = target_label.get_attribute('aria-checked')
                        if aria_checked == 'true':
                            print("   ✅ 선택 성공 (aria-checked)")
                            return
                        
                        # 8. 실패 시 로그만 출력 (재클릭하면 토글되어 해제될 수 있음)
                        print("   ⚠️ 선택 확인 실패 - 스크린샷으로 확인 필요")
                        all_labels = section.locator('label').all_inner_texts()
                        print(f"      (섹션 옵션: {all_labels})")

                    except Exception as e:
                        print(f"   ❌ 에러: {e}")
                        import traceback
                        traceback.print_exc()

                smart_select("타입", user['type'], "6️⃣")
                smart_select("소득", user['income'], "7️⃣")
                smart_select("지역", user['region'], "8️⃣")
                smart_select("자산", user['asset'], "9️⃣")
                smart_select("주택", user['house'], "🔟")
                smart_select("개인정보", "동의", "1️⃣1️⃣")

                # =========================================================
                # 제출
                # =========================================================
                print("\n📸 제출 전 최종 스크린샷: final_check.png")
                page.screenshot(path=f"final_check_{user['name']}.png", full_page=True)

                if DO_ACTUAL_SUBMIT:
                    print("🚀 제출 버튼 클릭...")
                    submit_btn = page.locator('#nsv_page_control_submit')
                    
                    if submit_btn.is_enabled():
                        submit_btn.click()
                        try:
                            # 완료 페이지나 메시지 대기
                            page.wait_for_function("""
                                () => {
                                    return window.location.href.includes('response') === false || 
                                           document.body.innerText.includes('완료') ||
                                           document.body.innerText.includes('접수');
                                }
                            """, timeout=10000)
                            print("🎉 제출 완료!")
                        except Exception as e:
                            print(f"❓ 제출 확인 실패: {e}")
                            # 일부 폼은 URL 변화 없이 완료 토스트만 노출됨
                            body_text = page.inner_text("body") if page.locator("body").count() else ""
                            if "완료" in body_text or "접수" in body_text:
                                print("🎉 텍스트 기준 완료로 간주")
                            else:
                                print("⚠️ 완료 텍스트 미확인, 스크린샷 확인 필요")
                    else:
                        print("🚫 제출 버튼이 비활성화 상태입니다. (필수값 누락)")
                else:
                    print("⏸️  테스트 모드 (제출 스킵)")

                if idx < len(USERS): time.sleep(2)

        except Exception as e:
            print(f"\n❌ 전체 프로세스 오류: {e}")
            page.screenshot(path="fatal_error.png")
        finally:
            print("\n⏳ 브라우저 종료")
            browser.close()

if __name__ == "__main__":
    run_automation()