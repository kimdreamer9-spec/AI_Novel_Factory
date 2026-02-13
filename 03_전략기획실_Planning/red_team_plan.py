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

# 1. 환경 및 경로 설정
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent                # 03_전략기획실_Planning
PROJECT_ROOT = PLANNING_DIR.parent                     # Root (AI_Novel_Factory)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

client = None
if OPENAI_KEY:
    try: client = OpenAI(api_key=OPENAI_KEY)
    except: pass

if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

# 2. 데이터 경로 (감시 대상)
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

# 참조: 작법 공식 (Logic Check)
RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
TREND_REPORT = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
TIP_DIR = BASE_INFO_DIR / "05_팁_보물창고"

# 감시: 성공작 DB (표절 방지용)
STORY_ANALYSIS_DIR = ANALYSIS_DIR / "03_스토리_분석"
CHAR_ANALYSIS_DIR = ANALYSIS_DIR / "02_캐릭터_분석"

# ---------------------------------------------------------
# 3. [Function] 표절 검사용 데이터 수집
# ---------------------------------------------------------
def get_benchmark_stories():
    """
    [RAG] 03_스토리_분석 폴더에 있는 성공작들의 줄거리를 긁어옵니다.
    """
    benchmarks = ""
    if STORY_ANALYSIS_DIR.exists():
        files = list(STORY_ANALYSIS_DIR.glob("*.json"))
        # 토큰 절약을 위해 랜덤 3개 + 대표작 1개 정도만 샘플링 (실제론 Vector DB 필요)
        selected = random.sample(files, min(len(files), 3))
        
        for f in selected:
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                title = data.get("title", "Unknown")
                # 줄거리나 로그라인 추출
                summary = data.get("synopsis", "") or data.get("logline", "")
                benchmarks += f"\n[Compare Target: {title}]\n{summary[:500]}...\n"
            except: pass
            
    return benchmarks

def extract_banned_keywords():
    """
    [Blacklist] 기존 작품의 고유명사(이름) 추출
    """
    banned_list = set()
    if CHAR_ANALYSIS_DIR.exists():
        for f in CHAR_ANALYSIS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                chars = data.get('characters', [])
                for c in chars:
                    if isinstance(c, dict) and 'name' in c:
                        banned_list.add(c['name'])
            except: pass
    return list(banned_list)

def gather_evidence():
    context = {
        "rubric": "No Rubric",
        "trend": "No Trend",
        "tips": "",
        "banned_words": [],
        "benchmarks": ""
    }
    if RUBRIC_FILE.exists(): context["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    if TREND_REPORT.exists(): context["trend"] = TREND_REPORT.read_text(encoding='utf-8')
    
    if TIP_DIR.exists():
        tips = list(TIP_DIR.rglob("*.md"))
        if tips:
            selected = random.sample(tips, min(len(tips), 3))
            for t in selected:
                context["tips"] += f"\n[Writing Rule: {t.name}]\n{t.read_text(encoding='utf-8')[:1000]}\n"

    context["banned_words"] = extract_banned_keywords()
    context["benchmarks"] = get_benchmark_stories()
    
    return context

# ---------------------------------------------------------
# 4. [Engine] AI 호출 (Logic First)
# ---------------------------------------------------------
def call_openai_smartest(prompt):
    candidate_models = ["gpt-5.2", "o3-mini", "gpt-5.3-codex"]
    for model_id in candidate_models:
        try:
            print(f"👹 [Red Team] Scanning with: {model_id}...")
            if "o3" in model_id:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": f"System: Plagiarism/Logic Scanner (JSON).\n\nUser: {prompt}"}]
                )
            else:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": "You are a Plagiarism & Logic Scanner. Return JSON Only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2 # 검증은 엄격하게
                )
            return response.choices[0].message.content.strip()
        except: continue
    return None

# ---------------------------------------------------------
# 5. [Core] 비평 실행 (유사도 계산 포함)
# ---------------------------------------------------------
def critique_plan(plan_json, round_num):
    print(f"\n👹 [Red Team] 기획안 V{round_num} 표절률 및 논리 정밀 진단 중...")
    
    evidence = gather_evidence()
    banned_str = ", ".join(evidence['banned_words'][:50])

    prompt = f"""
    # Role
    You are **Korea's Strictest Web Novel Logic & Ethics Officer**.
    Your goal is to detect **Plagiarism** and **Logical Flaws**.

    # [Task 1: Plagiarism Check]
    Compare the target plan with the [Benchmark Stories] below.
    - **Genre Tropes (Allowed):** Regression, Status Window, Dungeon, Revenge. (Do not count as plagiarism)
    - **Specific Plot/Settings (Banned):** Same character names, exact same sequence of events, same unique abilities.
    
    [Benchmark Stories (Existing Hits)]:
    {evidence['benchmarks']}
    
    [Banned Names]: [{banned_str}, ...]

    # [Task 2: Logic & Trend Check]
    - Does it follow the [Market Trend]?
    - Is the [Writing Formula] (e.g., Intro Hook) applied correctly?

    # Target Plan
    {json.dumps(plan_json, ensure_ascii=False, indent=2)}

    # Output Requirement
    - **Calculate 'Similarity Score' (0-100%)**: How much does this story resemble specific existing novels? (Exclude genre clichés).
    - **Threshold**: 
        - If Similarity <= 50%: **PASS** (Safe).
        - If Similarity > 50%: **REJECT** (Too similar to [Novel Name]).
    - Output **JSON ONLY**.

    # Output JSON Structure
    {{
        "score": (0-100 Integer, Overall Quality),
        "similarity_rate": (0-100 Integer, Plagiarism Risk),
        "status": "PASS" (if score >= 85 AND similarity_rate <= 50) else "REJECT",
        "critique_summary": "Summary of flaws or praise.",
        "fatal_flaws": [
            "1. Plagiarism Warning: Similarity with [Novel Name] is 65%...",
            "2. Logic Error: ...",
            "3. Banned Name Usage: ..."
        ],
        "improvement_instructions": "Specific feedback to fix logic and lower similarity."
    }}
    """

    result_text = None

    if client:
        result_text = call_openai_smartest(prompt)

    if not result_text and GEMINI_KEY:
        try:
            backup_model = genai.GenerativeModel("gemini-3-pro") 
            res = backup_model.generate_content(prompt)
            result_text = res.text.strip()
        except: pass

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
        return json.dumps({"score": 0, "status": "FATAL", "critique_summary": "AI Error"}, ensure_ascii=False)