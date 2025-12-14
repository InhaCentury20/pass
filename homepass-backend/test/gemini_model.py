import google.generativeai as genai

# 본인의 API 키 입력
GEMINI_API_KEY = "AIzaSyBapoa_N8v2asWfubwscwQVL8kgzrllnLk"
genai.configure(api_key=GEMINI_API_KEY)

print("🔍 사용 가능한 모델 리스트 확인 중...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"에러 발생: {e}")