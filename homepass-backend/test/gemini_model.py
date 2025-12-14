import time
import json
import traceback
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# ============================================================
# ⚙️ [설정]
# ============================================================
TARGET_FORM_URL = "https://form.naver.com/response/9YZljQp2eaxRn5IxDnbDJQ"
DO_ACTUAL_SUBMIT = True  # True: 실제 제출, False: 제출 버튼 누르기 전 종료

# 🔑 제공해주신 API 키
GEMINI_API_KEY = "AIzaSyDWCJ6plxNWULA27Crt7kLK_W0sTYw2fp4"

# ============================================================
# 👥 [사용자 데이터]
# ============================================================
USERS = [
    {
        "name": "김철수",
        "phone": "010-1111-1111",
        "birthdate": "20000729",  # 8자리 텍스트 (규칙 기반 입력용)
        "address_keyword": "통일로 838-21",
        "address_detail": "101호",
        "email": "kim@test.com",
        "type": "청년 일반공급 17.05",
        "income": "1",
        "region": "1",
        "asset": "해당없음",
        "house": "미소유",
        # AI가 추론할 때 사용할 추가 문맥 정보 (규칙에 없는 질문이 나올 경우 대비)
        "extra_profile": "나는 결혼하지 않은 미혼 청년이고, 차량도 없고 집도 없어. 개인정보 수집에는 동의해."
    }
]

# ============================================================
# 🤖 [AI 설정]
# ============================================================
genai.configure(api_key=GEMINI_API_KEY)

# 요청하신 2.5 Flash (API 모델명은 gemini-2.0-flash-exp 또는 1.5-flash 권장)
# 만약 2.0 모델 에러가 나면 'gemini-1.5-flash'로 변경하세요.
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
except:
    model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_answer(user_profile, question_title, options):
    """
    AI에게 질문과 옵션을 보내고 정답을 받아오는 함수
    """
    print(f"   🤖 [AI] 질문 분석 중: {question_title}")
    
    prompt = f"""
    You are a smart form assistant.
    Based on the USER PROFILE, select the best option for the QUESTION from the OPTIONS list.
    
    [USER PROFILE]
    {json.dumps(user_profile, ensure_ascii=False)}

    [QUESTION]
    {question_title}

    [OPTIONS]
    {json.dumps(options, ensure_ascii=False)}

    [INSTRUCTION]
    1. Select one option that best matches the user profile.
    2. If it's an agreement question, assume the user agrees.
    3. Return ONLY the JSON object. No markdown.
    4. Format: {{ "answer": "Exact Option Text" }}
    """
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        # 가끔 앞뒤에 다른 텍스트가 붙을 수 있어 { } 구간만 추출
        if "{" in clean_text:
            clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            
        result = json.loads(clean_text)
        return result.get("answer", "")
    except Exception as e:
        print(f"   ⚠️ AI 응답 처리 실패: {e}")
        return None

# ============================================================
# 🔧 [핵심 유틸리티 함수]
# ============================================================
def force_react_change(page, selector, value):
    """
    React/Vue 등 SPA 프레임워크에서 input/textarea 값을 강제로 변경하고 
    이벤트를 발생시켜 상태(State)를 업데이트하는 핵심 함수.
    """
    page.evaluate(f"""
        () => {{
            const el = document.querySelector('{selector}');
            if (el) {{
                // 1. 원본 Setter 호출 (React Hook 우회)
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, "value"
                ).set;
                
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

def check_and_fill_missing_with_ai(page, user):
    """
    제출 전 미입력 항목을 찾아 AI로 채우는 함수
    """
    print("\n🔍 [AI 검사] 미입력 항목 스캔 및 자동 채우기 시작...")
    
    # 모든 질문 그룹 가져오기
    questions = page.locator('div[role="group"]').all()
    
    for q in questions:
        try:
            # 질문 제목 확인 (제목이 없으면 패스)
            title_el = q.locator('.nsv_survey_reply_question_title, .questionTitle')
            if title_el.count() == 0: continue
            
            title = title_el.inner_text().replace("답변 필수", "").strip()
            
            # --- 입력 여부 판단 ---
            is_answered = False
            
            # 1. 텍스트 입력창 확인
            inputs = q.locator('input[type="text"], input[type="tel"], input[type="email"], textarea').all()
            for inp in inputs:
                if inp.input_value().strip():
                    is_answered = True
                    break
            
            # 2. 선택형(체크/라디오) 확인
            if not is_answered:
                # 네이버 폼은 aria-checked 또는 input:checked 사용
                checked_opts = q.locator('input:checked, [aria-checked="true"]').count()
                if checked_opts > 0:
                    is_answered = True
            
            # --- 미입력 시 AI 동작 ---
            if not is_answered:
                print(f"   ❗ 미입력 항목 발견: [{title}]")
                
                # 옵션들 텍스트 추출
                labels = q.locator('label').all_inner_texts()
                
                if not labels:
                    print("      (객관식이 아니거나 라벨을 못 찾아 AI 패스)")
                    continue
                
                # AI 호출
                ai_answer = get_ai_answer(user, title, labels)
                
                if ai_answer:
                    print(f"      ✨ AI 추천 답변: {ai_answer}")
                    
                    # 텍스트가 일치하는 라벨 찾기 (정확도 높이기 위해 filter 사용)
                    target_label = q.locator('label').filter(has_text=ai_answer).first
                    
                    if target_label.count() > 0:
                        # JS로 강제 클릭 (가장 확실함)
                        target_label.evaluate("el => el.click()")
                        time.sleep(0.5)
                        
                        # 체크 확인
                        if target_label.get_attribute('aria-checked') == 'true' or q.locator('input:checked').count() > 0:
                            print("      ✅ AI 답변 선택 완료")
                        else:
                            print("      ⚠️ 선택 실패 (클릭은 했으나 반응 없음)")
                    else:
                        print(f"      ❌ 화면에서 '{ai_answer}' 옵션을 찾을 수 없음")
                else:
                    print("      ⚠️ AI가 답변을 생성하지 못함")
                    
        except Exception as e:
            # 에러가 나도 멈추지 않고 다음 질문 검사
            print(f"   ⚠️ 검사 중 에러(무시하고 진행): {e}")

# ============================================================
# 🚀 [메인 실행 로직]
# ============================================================
def run_automation():
    with sync_playwright() as p:
        # 브라우저 실행 (헤드리스 끔)
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 타임아웃 넉넉히 설정
        page.set_default_timeout(30000)

        try:
            for idx, user in enumerate(USERS, 1):
                print(f"\n{'='*60}")
                print(f"▶ [{idx}/{len(USERS)}] 사용자 '{user['name']}' 처리 시작")
                print(f"{'='*60}\n")

                print(f"🌐 접속 중: {TARGET_FORM_URL}")
                page.goto(TARGET_FORM_URL, wait_until='networkidle')

                # 로그인 감지
                if "nid.naver.com" in page.url:
                    print("🔐 로그인 필요 (60초 대기)... 로그인 해주세요.")
                    page.wait_for_url("**/form.naver.com/response/**", timeout=60000)
                    print("✅ 로그인 완료")
                    page.wait_for_load_state('networkidle')
                
                # 폼 로딩 대기
                page.wait_for_selector('div[role="group"]', state='visible')
                print("📝 [1단계] 규칙 기반(Rule-Based) 입력 시작\n")

                # ---------------------------------------------------------
                # 1. 이름 & 2. 연락처
                # ---------------------------------------------------------
                try:
                    print(f"1️⃣ 이름: {user['name']}")
                    page.locator('div[role="group"][aria-label*="이름"] input').fill(user['name'])
                    
                    print(f"2️⃣ 연락처: {user['phone']}")
                    page.locator('div[role="group"][aria-label*="연락처"] input').fill(user['phone'].replace('-', ''))
                except Exception as e:
                    print(f"   ❌ 기본정보 입력 실패: {e}")

                # ---------------------------------------------------------
                # 3. 생년월일 (Textarea에 텍스트 입력)
                # ---------------------------------------------------------
                print(f"3️⃣ 생년월일: {user['birthdate']}")
                try:
                    # div[role="group"] 안의 textarea 찾기
                    textarea = page.locator('div[role="group"][aria-label*="생년월일"] textarea')
                    if textarea.count() > 0:
                        # React 강제 주입 함수 사용 (가장 안전)
                        force_react_change(page, 'div[role="group"][aria-label*="생년월일"] textarea', user['birthdate'])
                        print("   ✅ 입력 완료")
                    else:
                        print("   ❌ 생년월일 입력창을 찾을 수 없음")
                except Exception as e:
                    print(f"   ❌ 실패: {e}")

                # ---------------------------------------------------------
                # 4. 주소 (모달 검색 + 상세주소 강제 주입)
                # ---------------------------------------------------------
                print(f"4️⃣ 주소: {user['address_keyword']}")
                try:
                    addr_group = page.locator('div[role="group"][aria-label*="주소"]')
                    
                    # 1. 검색 버튼 클릭
                    addr_group.locator('button', has_text='주소검색').click()
                    
                    # 2. 모달 대기
                    modal = page.locator('.nsv_layer_postcode')
                    modal.wait_for(state='visible')
                    
                    # 3. 검색어 입력 및 찾기
                    modal.locator('input.nsv_layer_postcode_search_input').fill(user['address_keyword'])
                    modal.locator('button.nsv_layer_button_postcode_search').click()
                    
                    # 4. 결과 클릭
                    result_btn = modal.locator('ul.nsv_layer_address_list li button').first
                    result_btn.wait_for(state='visible')
                    result_btn.click()
                    
                    # 5. [동기화] 상세주소 입력창 활성화 대기
                    print("   ⏳ 주소 반영 대기...")
                    detail_input_loc = addr_group.locator('input[type="text"]').nth(1)
                    detail_input_loc.wait_for(state='visible', timeout=5000)
                    time.sleep(1) 

                    # 6. 상세주소 입력 (강제 주입)
                    detail_selector = 'div[role="group"][aria-label*="주소"] input[placeholder*="상세"]'
                    force_react_change(page, detail_selector, user['address_detail'])
                    
                    print(f"   ✅ 상세주소 입력 완료: {user['address_detail']}")
                    
                except Exception as e:
                    print(f"   ❌ 주소 실패: {e}")
                    # 모달 닫기 시도
                    if page.locator('.nsv_layer_button_close').is_visible():
                        page.locator('.nsv_layer_button_close').click()

                # ---------------------------------------------------------
                # 5. 이메일
                # ---------------------------------------------------------
                try:
                    print(f"5️⃣ 이메일: {user['email']}")
                    page.locator('div[role="group"][aria-label*="이메일"] input').fill(user['email'])
                except: pass

                # ---------------------------------------------------------
                # 6~11. 선택형 항목 (규칙 기반)
                # ---------------------------------------------------------
                def smart_select(label_keyword, option_keyword):
                    try:
                        section = page.locator(f'div[role="group"][aria-label*="{label_keyword}"]')
                        # 텍스트로 찾기
                        target = section.locator('label').filter(has_text=option_keyword).first
                        # 숫자로 찾기 fallback
                        if not target.count() and option_keyword.isdigit():
                            idx = int(option_keyword) - 1
                            target = section.locator(f'label[for*="item-{idx}"]').first
                        
                        # 클릭 실행 (JS)
                        if target.count(): 
                            target.evaluate("el => el.click()")
                    except: pass

                smart_select("타입", user['type'])
                smart_select("소득", user['income'])
                smart_select("지역", user['region'])
                smart_select("자산", user['asset'])
                smart_select("주택", user['house'])
                smart_select("개인정보", "동의")

                # ---------------------------------------------------------
                # [2단계] AI 미입력 검사 및 채우기 (NEW)
                # ---------------------------------------------------------
                # 규칙으로 채우지 못한 부분(오타, 구조 변경 등)을 AI가 마무리합니다.
                check_and_fill_missing_with_ai(page, user)

                # ---------------------------------------------------------
                # 제출
                # ---------------------------------------------------------
                print("\n📸 제출 전 최종 스크린샷: final_check.png")
                page.screenshot(path=f"final_check_{user['name']}.png", full_page=True)

                if DO_ACTUAL_SUBMIT:
                    print("🚀 제출 버튼 클릭...")
                    submit_btn = page.locator('#nsv_page_control_submit')
                    
                    if submit_btn.is_enabled():
                        submit_btn.click()
                        try:
                            # 완료 대기 (URL 변경 or 완료 텍스트)
                            page.wait_for_function("""
                                () => {
                                    return window.location.href.includes('response') === false || 
                                           document.body.innerText.includes('완료') ||
                                           document.body.innerText.includes('접수');
                                }
                            """, timeout=10000)
                            print("🎉 제출 성공!")
                        except Exception as e:
                            print(f"❓ 완료 상태 확인 실패: {e}")
                    else:
                        print("🚫 제출 버튼이 비활성화 상태입니다. (AI로도 해결 못한 필수값 존재)")
                else:
                    print("⏸️  테스트 모드 (제출 스킵)")

                if idx < len(USERS): time.sleep(2)

        except Exception as e:
            print(f"\n❌ 전체 프로세스 오류: {e}")
            traceback.print_exc()
            page.screenshot(path="fatal_error.png")
        finally:
            print("\n⏳ 브라우저 종료")
            time.sleep(2)
            browser.close()

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║      네이버폼 자동화 v4.0 (Rule-Based + AI Hybrid)           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    run_automation()