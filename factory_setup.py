import os
import json
import yaml  # PyYAML 필요 (없으면 pip install PyYAML)
from pathlib import Path

# =========================================================
# 🏭 [AI 소설 공장] 통합 구축 스크립트 (All-in-One)
# =========================================================

BASE_DIR = Path.cwd()

# ---------------------------------------------------------
# 1. 프롬프트 데이터 (YAML 내용 정의)
# ---------------------------------------------------------
PROMPTS_DATA = {
    "creative_new.yaml": """system: |
  You are **Korea's No.1 Web Novel CP (Creative Planner)**.
  Current Era: 2026. The market demands **Fast Pacing** and **Clear Rewards**.
  [🚨 CRITICAL] LANGUAGE: **KOREAN ONLY**. SYNOPSIS: **Ep 1~5 Detailed**.

user: |
  [Mission]: Create a top-tier web novel plan.
  [Ref]: {materials}
  [Rules]: {rules}
  [Input]: "{user_input}"
  [Feedback]: "{feedback}"
  
  [Output JSON Structure]
  {{ "title": "...", "genre": "...", "logline": "...", "characters": [], "synopsis": "...", "episode_plots": [], "swot_analysis": {{}} }}
""",
    "creative_fix.yaml": """system: |
  You are an expert **Web Novel Editor**.
  Goal: **MODIFY** plan based on feedback. **OUTPUT: KOREAN**.

user: |
  [Original]: {original_plan}
  [Feedback]: "{user_feedback}"
  [Mission]: Reflect feedback, Keep JSON structure, 5 Ep details.
""",
    "red_team.yaml": """system: |
  You are **Korea's Most Critical Web Novel Editor**.
  **OUTPUT: KOREAN**.

user: |
  [Ref]: {benchmarks}
  [Banned]: {banned_words}
  [Target]: {plan_json}
  [Mission]: Critique (Plagiarism, Logic, Commercial). Output JSON.
"""
}

# ---------------------------------------------------------
# 2. 프롬프트 로더 (Python Code)
# ---------------------------------------------------------
LOADER_CODE = """import yaml
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROMPT_DIR = CURRENT_DIR / "prompts"

def load_prompt(filename, **kwargs):
    try:
        file_path = PROMPT_DIR / filename
        if not file_path.exists(): return f"Error: {filename} not found", ""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        sys_p = data.get('system', '')
        usr_p = data.get('user', '')
        if kwargs:
            try:
                sys_p = sys_p.format(**kwargs)
                usr_p = usr_p.format(**kwargs)
            except: pass
        return sys_p, usr_p
    except: return "", ""
"""

# ---------------------------------------------------------
# 3. 공장 구조 설계도 (Infrastructure)
# ---------------------------------------------------------
STRUCTURE = {
    "00_기준정보_보물창고": {
        "files": ["standard-rubric.json", "rubric_maker.py"],
        "subdirs": {
            "04_설정_트랜드": [],
            "05_팁_보물창고": [],
            "작법_이론서": ["PD_작법서_요약.txt"],
            "99_지능형_프롬프트": ["01_Tree_of_Thoughts.md", "02_Self_Reflection.md", "04_RAG_Search_Augmented.md", "05_Reason_and_Act.md"]
        }
    },
    "01_자료실_Raw_Data": {
        "files": [], # 코드는 99_시스템_도구함으로 이동됨
        "subdirs": {
            "99_이미지_투입구": [],
            "99_텍스트_투입구": [],
            "00_성공작_아카이브": []
        }
    },
    "02_분석실_Analysis": {
        "files": ["master_analyst.py", "00_통합_트렌드_리포트.json"],
    },
    "03_전략기획실_Planning": {
        "files": ["creative_planner.py", "red_team_plan.py", "strategy_judge.py", "manager_development.py", "ui_planning.py", "ui_warehouse.py", "prompt_loader.py"],
        "subdirs": {
            "prompts": [] # 여기에 YAML 파일 들어감
        }
    },
    "04_설정_자료집": {
        "subdirs": {
            "A_대체역사_1800_2000": ["역사_연표_미국.txt"],
            "B_현대판타지_1950_2026": ["01_경제_역사", "02_기업_역사"],
            "C_공통_자료실": ["감정_표현_사전.txt"]
        }
    },
    "05_제작_스튜디오_Production": {
        "files": ["treatment_writer.py", "main_writer.py", "character_bot.py", "red_team_pd.py", "ui_production.py", "narrative_extractor.py"]
    },
    "06_품질관리_QC": {
        "files": ["final_polisher.py"]
    },
    "99_시스템_도구함": {
        "files": ["processor_pro.py", "scanner_pro.py", "text_importer.py", "check_api_status.py"]
    }
}

# ---------------------------------------------------------
# 4. 건설 로직 (Builder)
# ---------------------------------------------------------
def create_structure(base, structure):
    for name, content in structure.items():
        path = base / name
        
        if isinstance(content, dict): # 폴더
            path.mkdir(parents=True, exist_ok=True)
            print(f"📂 폴더: {name}")
            
            # 파일 생성
            if "files" in content:
                for file in content["files"]:
                    file_path = path / file
                    if not file_path.exists():
                        # 특수 파일 처리 (내용 채우기)
                        if file == "prompt_loader.py":
                            file_path.write_text(LOADER_CODE, encoding='utf-8')
                            print(f"  └─ ⚡ 생성 및 코드 주입: {file}")
                        else:
                            file_path.touch()
                            print(f"  └─ 📄 빈 파일 생성: {file}")
            
            # 하위 폴더 생성
            if "subdirs" in content:
                create_structure(path, content["subdirs"])
                
                # 프롬프트 YAML 주입 (03_전략기획실/prompts)
                if name == "03_전략기획실_Planning" and "prompts" in content["subdirs"]:
                    prompt_path = path / "prompts"
                    for fname, text in PROMPTS_DATA.items():
                        (prompt_path / fname).write_text(text, encoding='utf-8')
                        print(f"  └─ 📝 프롬프트 생성: prompts/{fname}")

        elif isinstance(content, list): # 단순 리스트
            path.mkdir(parents=True, exist_ok=True)
            for item in content:
                if "." in item:
                    (path / item).touch()
                else:
                    (path / item).mkdir(exist_ok=True)

def main():
    print(f"🚀 [Factory Setup] 통합 구축 시작...\n")
    
    # 1. 구조 생성
    create_structure(BASE_DIR, STRUCTURE)
    
    # 2. 루트 파일
    root_files = ["app.py", "model_selector.py", "system_utils.py", "requirements.txt", ".gitignore"]
    for f in root_files:
        if not (BASE_DIR / f).exists():
            (BASE_DIR / f).touch()
            print(f"📦 루트 파일 생성: {f}")

    # 3. .env (없을 때만)
    if not (BASE_DIR / ".env").exists():
        (BASE_DIR / ".env").write_text("GEMINI_API_KEY=\nOPENAI_API_KEY=", encoding='utf-8')
        print("🔑 .env 생성 완료")

    print("\n🎉 [Complete] 공장 구축 완료! (프롬프트 시스템 포함)")

if __name__ == "__main__":
    main()