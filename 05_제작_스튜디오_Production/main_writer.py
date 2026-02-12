import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SETTING_DIR = PROJECT_ROOT / "04_설정_자료집"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_WRITER") or os.getenv("GEMINI_API_KEY")
if API_KEY: genai.configure(api_key=API_KEY)

try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
    writer_model = genai.GenerativeModel(MODEL_NAME)
    print(f"🔥 [Main Writer] Engine: {MODEL_NAME}")
except ImportError:
    writer_model = None

def fetch_writing_assets():
    """설정 자료(세계관, 마법 등) 로드"""
    context = ""
    try:
        settings = list(SETTING_DIR.rglob("*.txt"))
        for f in settings[:5]: 
            context += f"\n[Setting: {f.name}]\n{f.read_text(encoding='utf-8')[:1000]}\n"
            
        tips = list(TIP_DIR.glob("*문장*.md")) + list(TIP_DIR.glob("*묘사*.txt"))
        for t in tips[:3]:
            context += f"\n[Style Tip: {t.name}]\n{t.read_text(encoding='utf-8')[:1000]}\n"
    except: pass
    return context

def write_episode(plan_data, treatment, episode_num=1):
    """트리트먼트 -> 본문 집필"""
    
    if not writer_model: return "❌ 오류: 엔진 로드 실패"
    
    assets = fetch_writing_assets()
    
    prompt = f"""
    You are a best-selling Web Novel Author in Korea.
    Write the **Full Manuscript** for **Episode {episode_num}**.
    
    [Model: {MODEL_NAME}]
    
    [Project Info]
    Title: {plan_data.get('title')}
    Genre: {plan_data.get('genre')}
    
    [Settings & Style (RAG)]
    {assets}
    
    [Blueprint (Treatment)]
    {treatment}
    
    [Writing Rules]
    1. Language: **Korean (Natural Web Novel Style)**
    2. Strictly follow the [Settings] (Magic names, locations, rules).
    3. Pacing: Fast, Immersive, Dopamine-inducing.
    4. Ending: Must be a **Cliffhanger**.
    5. Length: Approx 3000~5000 characters.
    
    [Output]
    Start writing the novel text directly. Do not include introductory remarks.
    """
    
    try:
        response = writer_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 본문 생성 실패: {e}"