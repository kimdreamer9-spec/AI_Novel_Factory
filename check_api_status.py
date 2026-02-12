import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI

# 1. 환경 변수 로드
current_dir = Path(__file__).resolve().parent
load_dotenv(current_dir / ".env")

print("\n" + "="*40)
print("🔌 [AI Factory] API 연결 정밀 진단")
print("="*40 + "\n")

# --- 1. Google Gemini 진단 ---
print("1️⃣ Google Gemini (Planning Engine)")
gemini_key = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("   🔴 키 없음 (Missing) - .env 파일을 확인하세요.")
else:
    print(f"   🟢 키 발견 (Found): {gemini_key[:5]}******")
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        res = model.generate_content("Hello")
        print("   ✅ [연결 성공] 응답:", res.text.strip())
    except Exception as e:
        print(f"   ❌ [연결 실패] 에러: {e}")

print("-" * 30)

# --- 2. OpenAI (Red Team Engine) ---
print("2️⃣ OpenAI (Red Team / Logic)")
openai_key = os.getenv("OPENAI_API_KEY")

if not openai_key:
    print("   🔴 키 없음 (Missing) - .env 파일을 확인하세요.")
    print("   ⚠️ 경고: .env 파일을 지우셨다면, 터미널이나 클라우드 Secret에 키를 등록해야 합니다!")
else:
    print(f"   🟢 키 발견 (Found): {openai_key[:5]}******")
    try:
        client = OpenAI(api_key=openai_key)
        # 가벼운 모델로 핑 테스트
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"   ✅ [연결 성공] 응답: {res.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ [연결 실패] 에러: {e}")

print("\n" + "="*40)