import os
import json
import sys
import random
from pathlib import Path
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# [Setup]
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 환경변수 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# 1. API 키 확보
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 2. 클라이언트 초기화
openai_client = None
if OPENAI_KEY:
    try: openai_client = OpenAI(api_key=OPENAI_KEY)
    except: pass

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# =========================================================
# 📂 [Data Collection] 누락되었던 RAG 기능 완전 복구
# =========================================================
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"
STORY_ANALYSIS_DIR = ANALYSIS_DIR / "03_스토리_분석"
CHAR_ANALYSIS_DIR = ANALYSIS_DIR / "02_캐릭터_분석"

def get_benchmark_stories():
    """성공작들의 줄거리를 긁어와 표절 대조군으로 삼습니다."""
    benchmarks = ""
    if STORY_ANALYSIS_DIR.exists():
        files = list(STORY_ANALYSIS_DIR.glob("*.json"))
        if files:
            selected = random.sample(files, min(len(files), 3)) # 토큰 절약 샘플링
            for f in selected:
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                    title = data.get("title", "Unknown")
                    summary = data.get("synopsis", "") or data.get("logline", "")
                    benchmarks += f"\n[Target: {title}]\n{summary[:500]}...\n"
                except: pass
    return benchmarks

def extract_banned_keywords():
    """기존 대박작들의 고유명사(이름)를 추출해 사용 금지어(Blacklist)로 만듭니다."""
    banned_list = set()
    if CHAR_ANALYSIS_DIR.exists():
        for f in CHAR_ANALYSIS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                for c in data.get('characters', []):
                    if isinstance(c, dict) and 'name' in c:
                        banned_list.add(c['name'])
            except: pass
    return list(banned_list)

def gather_evidence():
    context = {
        "rubric": "", "banned_words": [], "benchmarks": ""
    }
    RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
    if RUBRIC_FILE.exists(): context["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    
    context["banned_words"] = extract_banned_keywords()
    context["benchmarks"] = get_benchmark_stories()
    return context

# =========================================================
# 🧠 [Engine: 2026 Standard] GPT-5.2 최우선 호출
# =========================================================
def call_openai_smartest(prompt):
    if not openai_client: return None
    
    # 🔥 [2026 Model Priority]
    candidate_models = [
        "gpt-5.2",              # 1순위: 플래그십
        "gpt-5.1-thinking",     # 2순위: 추론 특화
        "gpt-5.3-codex-spark",  # 3순위: 초고속
        "o4-mini",              # 4순위: 고효율
        "gpt-4o"                # 5순위: 백업
    ]
    
    for model_id in candidate_models:
        try:
            print(f"👹 [Red Team] 접속 시도 중... 타겟: {model_id}")
            response = openai_client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a professional Web Novel Critic. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            print(f"✅ [Red Team] 연결 성공! 엔진: {model_id}")
            return response.choices[0].message.content.strip()
        except: 
            continue
            
    return None

def call_gemini_backup(prompt):
    try:
        import model_selector
        model_name = model_selector.find_best_model()
        model = genai.GenerativeModel(model_name)
        res = model.generate_content(prompt)
        return res.text.strip()
    except: return None

# =========================================================
# 🧨 [Execution] 비평 수행
# =========================================================
def critique_plan(plan_json, round_num):
    print(f"\n👹 [Red Team] 기획안 V{round_num} 정밀 진단 (GPT-5.2 Powered)...")
    
    evidence = gather_evidence()
    banned_str = ", ".join(evidence['banned_words'][:50])

    prompt = f"""
    You are **Korea's Most Critical Web Novel Editor (Red Team)** living in **2026**.
    
    [Mission]
    Analyze the plan below. Be harsh but constructive.
    
    [Reference Data]
    1. **Existing Hits (Check Plagiarism)**: {evidence['benchmarks']}
    2. **Banned Names**: {banned_str}
    
    [Thinking Process]
    1. **Plagiarism**: Is this too similar to the [Existing Hits]?
    2. **Logic**: Does the 'World View' make sense?
    3. **Commercial**: Will readers pay for this?
    
    [Target Plan]
    {json.dumps(plan_json, ensure_ascii=False, indent=2)}

    [Output Format (JSON Only)]
    {{
        "score": (Integer 0-100),
        "similarity_rate": (Integer 0-100, how similar to hits),
        "critique_summary": "Summary of critique.",
        "fatal_flaws": ["Flaw 1", "Flaw 2"],
        "improvement_instructions": "Specific fixes required."
    }}
    """

    result_text = None

    # 1. OpenAI 2026 모델 시도
    if openai_client:
        result_text = call_openai_smartest(prompt)

    # 2. Gemini 백업 시도
    if not result_text and GEMINI_KEY:
        result_text = call_gemini_backup(prompt)

    # 3. 결과 파싱
    if result_text:
        try:
            if "```json" in result_text: 
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text: 
                result_text = result_text.replace("```", "").strip()
            return json.loads(result_text)
        except:
            return {"score": 0, "critique_summary": "JSON Error", "fatal_flaws": ["Format Error"]}
    
    return {"score": 0, "critique_summary": "AI Error", "fatal_flaws": ["System Error"]}