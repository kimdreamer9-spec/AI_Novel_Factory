import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 1. 환경 변수 로드
current_dir = Path(__file__).resolve().parent
load_dotenv(current_dir / ".env")

# 2. 모델 셀렉터 호출
sys.path.append(str(current_dir))
from model_selector import find_best_model
target_model = find_best_model()

print("\n" + "="*50)
print(f"🔌 [AI Factory] 2026 Engine Status Check")
print("="*50 + "\n")

gemini_key = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("🔴 Google API Key: Missing")
else:
    print(f"🟢 Target Model: {target_model}")
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(target_model)
        # 2026년의 지능 테스트
        res = model.generate_content("2026년 한국 웹소설 시장의 핵심 트렌드 하나만 말해줘.")
        print(f"✅ [연결 성공] 응답: {res.text[:50]}...")
    except Exception as e:
        print(f"❌ [연결 실패] 에러: {e}")

print("\n" + "="*50)