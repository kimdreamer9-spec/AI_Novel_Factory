import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
import anthropic

# 1. 환경 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

def print_header(title):
    print(f"\n{'='*60}")
    print(f"📡 {title}")
    print(f"{'='*60}")

# ---------------------------------------------------------
# 1. Google Gemini Scanner
# ---------------------------------------------------------
def check_google():
    print_header("Google Gemini Available Models")
    api_key = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ API Key Missing (GEMINI_API_KEY)")
        return

    try:
        genai.configure(api_key=api_key)
        models = []
        for m in genai.list_models():
            # 텍스트 생성이 가능한 모델만 필터링
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
        
        models.sort() # 가나다순 정렬
        
        print(f"✅ Found {len(models)} models:")
        for name in models:
            # 보기 편하게 models/ 접두사 강조
            print(f"  - {name}")
            
    except Exception as e:
        print(f"❌ Error scanning Google: {e}")

# ---------------------------------------------------------
# 2. OpenAI Scanner
# ---------------------------------------------------------
def check_openai():
    print_header("OpenAI Available Models")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ API Key Missing (OPENAI_API_KEY)")
        return

    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        gpt_models = []
        for m in models.data:
            # 너무 잡다한 모델(dall-e, tts 등) 제외하고 GPT 계열만 확인
            if "gpt" in m.id or "o1" in m.id or "o3" in m.id:
                gpt_models.append(m.id)
        
        gpt_models.sort()
        
        print(f"✅ Found {len(gpt_models)} GPT-related models:")
        for name in gpt_models:
            print(f"  - {name}")
            
    except Exception as e:
        print(f"❌ Error scanning OpenAI: {e}")

# ---------------------------------------------------------
# 3. Anthropic (참고)
# ---------------------------------------------------------
def check_anthropic():
    print_header("Anthropic Claude Status")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ API Key Missing (ANTHROPIC_API_KEY)")
        return

    print("ℹ️ Note: Anthropic API does NOT support listing models programmatically.")
    print("ℹ️ You must check their official docs page.")
    print("✅ However, checking connection with a standard model...")
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # 가장 표준적인 모델로 연결 테스트만 수행
        client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("✅ Connection Successful (API Key is valid)")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    check_google()
    check_openai()
    check_anthropic()