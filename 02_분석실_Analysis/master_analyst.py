import os
import time
import json
import warnings
import re
import sys
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 👑 [통합 분석관] Master Analyst (V2026. Brain Connected)
# 역할: 성공작을 읽고 -> 지능형 프롬프트로 분석 -> JSON 데이터 추출
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

# 모델 선택 (분석은 논리력이 생명 -> 'logic' 모드)
try:
    from model_selector import find_best_model
    MODEL_NAME = find_best_model("logic")
except:
    MODEL_NAME = "gemini-1.5-flash"

print(f"🚀 [Master Analyst] 가동 (Engine: {MODEL_NAME})")
model = genai.GenerativeModel(MODEL_NAME)

# 경로 설정
RAW_DATA_DIR = PROJECT_ROOT / "01_자료실_Raw_Data" / "00_성공작_아카이브"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"
BRAIN_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "99_지능형_프롬프트"
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"

# ---------------------------------------------------------
# 🧠 [Brain Loader] 지능형 사고 회로 장착
# ---------------------------------------------------------
def load_brain(filename):
    path = BRAIN_DIR / filename
    if path.exists(): return path.read_text(encoding='utf-8')
    return ""

# 분석관에게 필요한 뇌: RAG(자료참조) + Self-Reflection(검증)
BRAIN_RAG = load_brain("04_RAG_Search_Augmented.md")
BRAIN_REFLECTION = load_brain("02_Self_Reflection.md")

# ---------------------------------------------------------
# 🛠️ [Utility] 스마트 로더 & 파서
# ---------------------------------------------------------
def load_smart_context(folder_path, limit=60000):
    """폴더 내 모든 MD 파일을 읽어 컨텍스트 확보"""
    full_text = ""
    md_files = sorted(list(folder_path.glob("*.md")))
    for f in md_files:
        try:
            text = f.read_text(encoding='utf-8')
            full_text += f"\n=== [File: {f.name}] ===\n{text}\n"
            if len(full_text) >= limit: break
        except: pass
    return full_text[:limit]

def extract_json_safely(text):
    """AI 답변에서 JSON만 추출"""
    try:
        if "```json" in text:
            return json.loads(text.split("```json")[1].split("```")[0].strip())
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match: return json.loads(match.group())
        return json.loads(text)
    except:
        return {"error": "JSON Parsing Failed", "raw": text[:500]}

def save_report(folder_name, category, data):
    target_dir = ANALYSIS_DIR / category
    target_dir.mkdir(parents=True, exist_ok=True)
    prefix = {"01_문체_분석":"STYLE", "02_캐릭터_분석":"CHAR", "03_스토리_분석":"STORY"}.get(category, "ANALYSIS")
    filename = f"{prefix}_{folder_name}.json"
    with open(target_dir / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"      💾 [Saved] {filename}")

# ---------------------------------------------------------
# 📝 [Prompt Engineering] 지능형 분석 프롬프트 조립
# ---------------------------------------------------------
def create_analysis_prompt(task_type, rubric, meta, text):
    
    # 1. 시스템 페르소나 (MD 파일 활용)
    system_instruction = f"""
    {BRAIN_RAG}
    
    [Additional Role]
    You are an **Elite Web Novel Analyst**.
    Your job is to extract the 'Winning Formula' from the provided novel text.
    Use **Self-Reflection** ({BRAIN_REFLECTION[:200]}...) logic to verify your analysis.
    """
    
    # 2. 분석 지시 (User Message)
    special_instruction = ""
    if "Character" in task_type:
        special_instruction = "Identify exactly **5 Key Characters** (Protagonist, Antagonist, Helper, Rival, Extra)."

    user_message = f"""
    [Task]: Analyze the provided novel text focusing on **{task_type}**.
    
    [Rubric Criteria]:
    {rubric[:1000]}
    
    [Novel Meta Info]:
    {meta[:500]}
    
    [Novel Text Content]:
    {text}
    
    [Special Instruction]:
    {special_instruction}
    
    [Output Format - JSON Only]:
    {{
        "title": "Title",
        "analysis_content": {{
            "description": "Deep dive analysis...",
            "key_elements": ["Element 1", "Element 2"],
            "character_list": ["Name (Role)", ...] 
        }},
        "evidence_from_text": "Direct Quote",
        "actionable_insight": "One strategy we can steal for our own novel"
    }}
    """
    
    return system_instruction, user_message

# ---------------------------------------------------------
# 🔥 [Main Logic] 전체 분석 실행
# ---------------------------------------------------------
def analyze_all():
    rubric_text = "Standard Criteria"
    if RUBRIC_FILE.exists(): rubric_text = RUBRIC_FILE.read_text(encoding='utf-8')

    targets = []
    if RAW_DATA_DIR.exists():
        for root, dirs, files in os.walk(RAW_DATA_DIR):
            path = Path(root)
            if any(f.endswith('.md') for f in files) and path != RAW_DATA_DIR:
                targets.append(path)
    
    if not targets:
        print("📭 분석할 작품이 없습니다.")
        return

    print(f"🔍 총 {len(targets)}개 작품 분석 시작...\n")

    for folder in targets:
        print(f"📘 [Target] {folder.name}")
        full_text = load_smart_context(folder)
        meta_data = ""
        for jf in folder.glob("*.json"):
            try: meta_data += jf.read_text(encoding='utf-8')
            except: pass

        # 3가지 관점 분석 (문체, 캐릭터, 스토리)
        tasks = [
            ("Writing Style & Pacing", "01_문체_분석"),
            ("Characters (5 Key Roles)", "02_캐릭터_분석"),
            ("Plot Structure & Hook", "03_스토리_분석")
        ]

        for task_name, category in tasks:
            try:
                # 지능형 프롬프트 생성
                sys_msg, usr_msg = create_analysis_prompt(task_name, rubric_text, meta_data, full_text)
                
                # 모델 호출 (System Instruction에 뇌 장착)
                model_instance = genai.GenerativeModel(MODEL_NAME, system_instruction=sys_msg)
                res = model_instance.generate_content(usr_msg)
                
                # 결과 저장
                data = extract_json_safely(res.text)
                if "error" not in data:
                    save_report(folder.name, category, data)
                else:
                    print(f"      🚨 {task_name} 파싱 실패")
            except Exception as e:
                print(f"      🚨 {task_name} 오류: {e}")
            
            time.sleep(1) # 쿨타임

        print("      ✅ 분석 완료.\n")

if __name__ == "__main__":
    analyze_all()