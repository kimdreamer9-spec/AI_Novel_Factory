import os
import json
import sys
import random
import time
from pathlib import Path
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 👹 [레드팀] Red Team Critic (Plagiarism & Logic Police)
# 역할: 서사적 논리 검증 + '성공작 DB'와의 스토리 유사도(%) 정밀 타격
# =========================================================

# 1. 환경 및 경로 설정 (절대 경로 보장)
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent                # 03_전략기획실_Planning
PROJECT_ROOT = PLANNING_DIR.parent                     # Root (AI_Novel_Factory)

# 시스템 경로 추가 (model_selector import를 위해)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 2. 클라이언트 초기화
client = None
if OPENAI_KEY:
    try: client = OpenAI(api_key=OPENAI_KEY)
    except: pass

if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

# 3. 데이터 경로 (감시 대상)
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

# 참조: 작법 공식
RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
TREND_REPORT = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
TIP_DIR = BASE_INFO_DIR / "05_팁_보물창고"

# 감시: 성공작 DB (표절 방지용)
STORY_ANALYSIS_DIR = ANALYSIS_DIR / "03_스토리_분석"
CHAR_ANALYSIS_DIR = ANALYSIS_DIR / "02_캐릭터_분석"

# ---------------------------------------------------------
# 4. [Function] 데이터 수집 (RAG)
# ---------------------------------------------------------
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
        "rubric": "", "trend": "", "tips": "",
        "banned_words": [], "benchmarks": ""
    }
    if RUBRIC_FILE.exists(): context["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    if TREND_REPORT.exists(): context["trend"] = TREND_REPORT.read_text(encoding='utf-8')
    
    if TIP_DIR.exists():
        tips = list(TIP_DIR.rglob("*.md")) + list(TIP_DIR.rglob("*.txt"))
        if tips:
            selected = random.sample(tips, min(len(tips), 3))
            for t in selected:
                context["tips"] += f"\n[Tip: {t.name}]\n{t.read_text(encoding='utf-8')[:1000]}\n"

    context["banned_words"] = extract_banned_keywords()
    context["benchmarks"] = get_benchmark_stories()
    return context

# ---------------------------------------------------------
# 5. [Engine] 최신 모델 호출 (OpenAI First)
# ---------------------------------------------------------
def call_openai_smartest(prompt):
    # 2026년 기준 최신 모델 순차 시도 (사장님 지시 준수)
    candidate_models = ["gpt-5.2", "o3-mini", "gpt-5.3-codex", "gpt-4o"]
    
    for model_id in candidate_models:
        try:
            print(f"👹 [Red Team] Scanning with: {model_id}...")
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a Plagiarism & Logic Scanner. JSON Only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2 # 검증은 엄격하게
            )
            return response.choices[0].message.content.strip()
        except: 
            continue # 실패하면 다음 모델 시도
            
    return None

# ---------------------------------------------------------
# 6. [Core] 비평 실행
# ---------------------------------------------------------
def critique_plan(plan_json, round_num):
    print(f"\n👹 [Red Team] 기획안 V{round_num} 정밀 진단 시작...")
    
    evidence = gather_evidence()
    banned_str = ", ".join(evidence['banned_words'][:50])

    # 사장님의 강력한 프롬프트 유지
    prompt = f"""
    # Role
    You are **Korea's Strictest Web Novel Logic & Ethics Officer**.
    Your goal is to detect **Plagiarism** and **Logical Flaws**.

    # [Task 1: Plagiarism Check]
    Compare the target plan with the [Benchmark Stories] below.
    - **Allowed Tropes**: Regression, Status Window, Dungeon, Revenge.
    - **Banned**: Same character names, exact same sequence of events.
    
    [Benchmark Stories]:
    {evidence['benchmarks']}
    
    [Banned Names]: [{banned_str}, ...]

    # [Task 2: Logic & Trend Check]
    - Does it follow the [Market Trend]?
    - Is the [Writing Formula] applied correctly?

    # Target Plan
    {json.dumps(plan_json, ensure_ascii=False, indent=2)}

    # Output Requirement
    - Output **JSON ONLY**.
    - **Similarity Score (0-100%)**:
        - <= 50%: PASS
        - > 50%: REJECT
    
    # Output JSON Structure
    {{
        "score": (0-100 Integer),
        "similarity_rate": (0-100 Integer),
        "status": "PASS" or "REJECT",
        "critique_summary": "Summary...",
        "fatal_flaws": ["1. ...", "2. ..."],
        "improvement_instructions": "Specific feedback..."
    }}
    """

    result_text = None

    # 1. OpenAI 시도
    if client:
        result_text = call_openai_smartest(prompt)

    # 2. Gemini 백업 (Model Selector 연동)
    if not result_text and GEMINI_KEY:
        try:
            # 여기서 404 안 나게 안전장치
            try:
                from model_selector import find_best_model
                backup_model_name = find_best_model()
            except:
                backup_model_name = "gemini-1.5-flash"
                
            print(f"⚠️ [Red Team] OpenAI 응답 없음 -> Gemini ({backup_model_name}) 투입")
            backup_model = genai.GenerativeModel(backup_model_name)
            res = backup_model.generate_content(prompt)
            result_text = res.text.strip()
        except Exception as e:
            print(f"❌ [Red Team] Gemini 백업 실패: {e}")

    # 3. 결과 파싱 및 반환
    if result_text:
        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.replace("```", "").strip()
            return result_text
        except:
            return json.dumps({"score": 50, "status": "ERROR", "critique_summary": "Format Error"}, ensure_ascii=False)
    else:
        # 모든 AI 실패 시
        return json.dumps({"score": 0, "status": "FATAL", "critique_summary": "AI Logic Error"}, ensure_ascii=False)