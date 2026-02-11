import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# 설정 로드
FIXED_ROOT = Path(r"C:\Users\msi\OneDrive\바탕 화면\AI_Novel_Factory_Final")
load_dotenv(dotenv_path=FIXED_ROOT / ".env")
genai.configure(api_key=os.getenv("GEMINI_KEY_PLANNING"))

print("🔍 [API 모델 명단 조회 중...]")
print("="*50)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            
    print("="*50)
    print("👉 위 목록에서 '3.0'이나 'exp'가 들어간 이름을 찾으세요.")
except Exception as e:
    print(f"❌ 에러 발생: {e}")