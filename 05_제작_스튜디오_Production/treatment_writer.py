import os
import json
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"
SETTING_DIR = PROJECT_ROOT / "04_설정_자료집"

# 루트 경로 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_WRITER") or os.getenv("GEMINI_API_KEY")
if API_KEY: genai.configure(api_key=API_KEY)

# 🔥 [모델 셀렉터] 무조건 최강 모델 로드
try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
    writer_model = genai.GenerativeModel(MODEL_NAME)
    print(f"🔥 [Treatment Writer] Engine: {MODEL_NAME}")
except ImportError:
    writer_model = None # 셀렉터 없으면 동작 안 함 (강제)

def fetch_plot_knowhow():
    """도입부, 플롯 구성 팁 로드"""
    context = ""
    try:
        tips = []
        for kw in ['도입부', '플롯', '구조', '전개']:
            tips.extend(list(TIP_DIR.glob(f"*{kw}*.md")))
            tips.extend(list(TIP_DIR.glob(f"*{kw}*.txt")))
        
        seen = set()
        for tip in tips[:5]:
            if tip.name not in seen:
                context += f"\n[Tip: {tip.name}]\n{tip.read_text(encoding='utf-8')[:1500]}\n"
                seen.add(tip.name)
    except: pass
    return context

def generate_treatment(plan_data, episode_num=1):
    """기획안 -> 씬(Scene) 설계도 변환"""
    
    if not writer_model:
        return "❌ 오류: model_selector.py가 루트에 없습니다."

    plot_tips = fetch_plot_knowhow()
    
    prompt = f"""
    You are the Lead Storyboard Artist for a top-tier web novel.
    Write a **Scene-by-Scene Treatment** for **Episode {episode_num}**.
    
    [Model: {MODEL_NAME}]
    
    [Project Info]
    - Title: {plan_data.get('title')}
    - Genre: {plan_data.get('genre')}
    - Logline: {plan_data.get('logline')}
    - Synopsis: {plan_data.get('synopsis')}
    - Ep 1 Core Points: {plan_data.get('ep1_core_points', {})}
    
    [Reference Tips (RAG)]
    {plot_tips}
    
    [Task]
    Break down Episode {episode_num} into 4~6 Scenes.
    For each scene, specify:
    1. **Header:** [Scene #] Location / Time
    2. **Characters:** Who?
    3. **Action:** What happens? (Specific details)
    4. **Conflict:** Tension point.
    5. **Objective:** Narrative purpose.
    
    [Output Format]
    Markdown format. Start with `# {plan_data.get('title')} - Episode {episode_num} Treatment`.
    Make sure to include a 'Hook' at the start and a 'Cliffhanger' at the end.
    """
    
    try:
        response = writer_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 트리트먼트 생성 실패: {e}"