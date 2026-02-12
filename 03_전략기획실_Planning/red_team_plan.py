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
# 역할: 서사적 논리 검증 + '성공작 DB'와의 표절/유사성 정밀 타격
# 타겟: 분석실 데이터(고유명사 필터링), 작법 공식(구조 검증)
# =========================================================

# ---------------------------------------------------------
# 1. 환경 및 경로 설정
# ---------------------------------------------------------
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent                # 03_전략기획실_Planning
PROJECT_ROOT = PLANNING_DIR.parent                     # Root (AI_Novel_Factory)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 클라이언트 초기화
client = None
if OPENAI_KEY:
    try: client = OpenAI(api_key=OPENAI_KEY)
    except: pass

if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

# ---------------------------------------------------------
# 2. 데이터 경로 (감시 대상)
# ---------------------------------------------------------
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

# 참조: 작법 공식
RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
TREND_REPORT = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
TIP_DIR = BASE_INFO_DIR / "05_팁_보물창고"

# 감시: 성공작 DB (표절 방지용)
CHAR_ANALYSIS_DIR = ANALYSIS_DIR / "02_캐릭터_분석"
STORY_ANALYSIS_DIR = ANALYSIS_DIR / "03_스토리_분석"
STYLE_ANALYSIS_DIR = ANALYSIS_DIR / "01_문체_분석"

# ---------------------------------------------------------
# 3. [Logic Check] 감시 로직
# ---------------------------------------------------------
FEW_SHOT_CRITIQUES = """
[Case 1 - Plagiarism (Name/Setting)]
Input: "주인공 강도준은 순양그룹의 막내아들로 회귀하여..."
Critique: "FATAL PLAGIARISM. '강도준', '순양그룹'은 <재벌집 막내아들>의 고유명사임. 설정은 참고하되 이름과 구체적 배경은 100% 창작해야 함. 수정 필수."

[Case 2 - Logic Error (Reaction)]
Input: "주인공이 미래 지식으로 반도체를 선점했는데, 삼성과 하이닉스가 아무런 견제도 안 함."
Critique: "LOGIC ERROR. 대기업이 경쟁자가 나타났는데 방관하는 건 비현실적임. 소송을 걸거나 인수 합병을 시도하는 등 '장애물(Crisis)'이 발생해야 함."

[Case 3 - Story Copycat]
Input: "주인공이 남미로 가서 독재자가 되는데, 친구 따라 강남 갔다가 장관이 된다."
Critique: "CONTENT COPY. <비자발적 종신 독재자>와 도입부 플롯이 너무 유사함. 클리셰(회귀/독재)는 쓰되, 계기(Trigger)나 전개 방식은 비틀어야 함."
"""

def extract_banned_keywords():
    """
    [Blacklist System] 분석실의 모든 JSON을 털어서 '고유명사(이름, 회사명)'를 추출
    """
    banned_list = set()
    
    # 1. 캐릭터 분석에서 이름 추출
    if CHAR_ANALYSIS_DIR.exists():
        for f in CHAR_ANALYSIS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                # Main/Sub 캐릭터 이름 수집
                if isinstance(data, dict):
                    # 구조에 따라 다를 수 있으니 유연하게 처리
                    chars = data.get('characters', []) or data.get('character_analysis', [])
                    for c in chars:
                        if isinstance(c, dict) and 'name' in c:
                            banned_list.add(c['name'])
            except: pass

    # 2. 스토리 분석에서 고유명사(키워드) 추출
    if STORY_ANALYSIS_DIR.exists():
        for f in STORY_ANALYSIS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                keywords = data.get('keywords', [])
                for k in keywords:
                    if len(k) > 2: # 너무 짧은 단어 제외
                        banned_list.add(k.replace("#", ""))
            except: pass
            
    return list(banned_list)

def gather_evidence():
    """
    RAG 데이터 수집 (작법 팁 + 트렌드 + 금지어 리스트)
    """
    context = {
        "rubric": "No Rubric",
        "trend": "No Trend",
        "tips": "",
        "banned_words": []
    }

    if RUBRIC_FILE.exists(): context["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    if TREND_REPORT.exists(): context["trend"] = TREND_REPORT.read_text(encoding='utf-8')

    # 작법 팁 (논리 검증용)
    if TIP_DIR.exists():
        tips = list(TIP_DIR.rglob("*.md"))
        if tips:
            selected = random.sample(tips, min(len(tips), 3))
            for t in selected:
                context["tips"] += f"\n[Writing Rule: {t.name}]\n{t.read_text(encoding='utf-8')[:1000]}\n"

    # 금지어 리스트 (표절 방지용)
    context["banned_words"] = extract_banned_keywords()

    return context

def call_openai_smartest(prompt):
    # 추론 중심 모델 호출 (Logic First)
    candidate_models = ["gpt-5.2", "o3-mini", "gpt-5.3-codex"]
    
    for model_id in candidate_models:
        try:
            print(f"👹 [Red Team] Scanning with: {model_id}...")
            if "o3" in model_id:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": f"System: Plagiarism & Logic Scanner (JSON).\n\nUser: {prompt}"}]
                )
            else:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": "You are a Plagiarism & Logic Scanner. Return JSON Only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2 # 표절 검사는 매우 엄격하게 (창의성 필요 없음)
                )
            return response.choices[0].message.content.strip()
        except: continue
    return None

def critique_plan(plan_json, round_num):
    print(f"\n👹 [Red Team] 기획안 V{round_num} 표절 및 논리 검증 중...")
    
    evidence = gather_evidence()
    banned_str = ", ".join(evidence['banned_words'][:50]) # 토큰 제한 고려 상위 50개만

    prompt = f"""
    # Role
    You are **Korea's Strictest Web Novel Ethics & Logic Officer**.
    Your mission is to prevent "Plagiarism" and ensure "Narrative Logic".

    # [CRITICAL] Plagiarism Check List (Banned Words from Database)
    The following names/keywords exist in existing hit novels. **DO NOT USE THEM.**
    Banned List: [{banned_str}, ...]
    
    # RAG Context (Standards)
    - [Market Trend]: {evidence['trend'][:1500]}
    - [Writing Formulas]: {evidence['tips']}

    # Target Plan
    {json.dumps(plan_json, ensure_ascii=False, indent=2)}

    # Audit Protocol (Step-by-Step)
    1. **Plagiarism Check**: 
       - Does the character name or setting appear in the [Banned List]?
       - Is the specific plot too similar to famous novels (e.g., 'Reborn Rich', 'The Dictator')?
       - **Action:** If similarity > 80%, REJECT immediately.
    2. **Logic Check (Butterfly Effect)**:
       - If protagonist changes history, does the world react?
       - Are the surrounding characters dynamic or static?
    3. **Formula Check**:
       - Does it follow the 3-Act Structure and Intro Formula?

    # Few-Shot Critiques
    {FEW_SHOT_CRITIQUES}

    # Output Requirement
    - Output **JSON ONLY**.
    - Language: Korean.

    # Output JSON Structure
    {{
        "score": (0-100 Integer),
        "status": "PASS" (score >= 85) or "REJECT",
        "critique_summary": "Summary of flaws.",
        "fatal_flaws": [
            "1. Plagiarism Warning: Used banned name 'Kang Do-jun'...",
            "2. Logic Error: ...",
        ],
        "improvement_instructions": "How to fix names and logic to avoid plagiarism."
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