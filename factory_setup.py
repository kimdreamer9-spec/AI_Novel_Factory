import os
import json
from pathlib import Path

# =========================================================
# 🏭 [AI 소설 공장] 인프라 구축 스크립트 (Infrastructure Only)
# 역할: 오직 '폴더'와 '파일'의 뼈대만 생성합니다. (내용은 나중에 채움)
# =========================================================

BASE_DIR = Path.cwd()

# 1. 공장 설계도 (Blueprint)
# 딕셔너리 키는 폴더명, 리스트는 그 안의 파일명입니다.
STRUCTURE = {
    "00_기준정보_보물창고": {
        "files": ["standard-rubric.json", "rubric_maker.py"],
        "subdirs": {
            "04_설정_트랜드": [],  # 추후 트렌드 리포트 저장
            "05_팁_보물창고": [],  # 작법 팁 저장
            "작법_이론서": [       # 텍스트 파일 껍데기만 생성
                "PD_작법서_요약.txt", 
                "유튜브_대사_필승공식.txt",
                "웹소설_기승전결_구조.txt"
            ],
            "99_지능형_프롬프트": [ # 프롬프트 파일 껍데기만 생성
                "01_Tree_of_Thoughts.md",
                "02_Self_Reflection.md",
                "03_Meta_Prompting.md",
                "04_RAG_Search_Augmented.md",
                "05_Reason_and_Act.md"
            ]
        }
    },
    "01_자료실_Raw_Data": {
        "files": ["processor_pro.py", "text_importer.py", "scanner_pro.py"],
        "subdirs": {
            "99_이미지_투입구": [],
            "99_텍스트_투입구": [],
            "00_성공작_아카이브": []
        }
    },
    "02_분석실_Analysis": {
        "files": ["staff_analyst.py", "leader_analyst.py", "00_통합_트렌드_리포트.json"],
        "subdirs": {
            "01_문체_분석": [],
            "02_캐릭터_분석": [],
            "03_스토리_분석": []
        }
    },
    "03_전략기획실_Planning": {
        "files": ["creative_planner.py", "red_team_plan.py", "strategy_judge.py", "ui_planning.py", "ui_warehouse.py"]
    },
    "04_설정_자료집": {
        "files": [],
        "subdirs": {
            "A_대체역사_1800_2000": ["역사_연표_미국.txt", "무기_개발_연표.txt", "발명품_목록.txt", "인재_목록.txt"],
            "B_현대판타지_1950_2026": [ # 하위 폴더는 아래 main()에서 추가 생성
                "01_경제_역사", "02_기업_역사", "03_인물_DB", "04_꿀템_치트키"
            ], 
            "C_공통_자료실": ["맛깔난_욕설모음.txt", "음식_묘사_사전.txt", "감정_표현_사전.txt"]
        }
    },
    "05_제작_스튜디오_Production": {
        "files": ["treatment_writer.py", "character_bot.py", "main_writer.py", "red_team_pd.py", "ui_production.py"]
    },
    "06_품질관리_QC": {
        "files": ["plagiarism_scanner.py", "final_polisher.py"]
    }
}

# =========================================================
# 🏗️ 건설 로직 (Builder)
# =========================================================
def create_structure(base, structure):
    for name, content in structure.items():
        path = base / name
        
        # 1. 폴더인 경우 (딕셔너리 구조)
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            print(f"📂 폴더 확인/생성: {name}")
            
            # 1-1. 해당 폴더 내 파일 생성
            if "files" in content:
                for file in content["files"]:
                    file_path = path / file
                    if not file_path.exists():
                        file_path.touch() # 빈 파일 생성
                        print(f"  └─ 📄 파일 생성: {file}")
            
            # 1-2. 서브 폴더 재귀 호출
            if "subdirs" in content:
                create_structure(path, content["subdirs"])
                
        # 2. 리스트인 경우 (단순 하위 폴더/파일 목록)
        elif isinstance(content, list):
            path.mkdir(parents=True, exist_ok=True)
            for item in content:
                # 확장자가 없으면 폴더로 간주, 있으면 파일로 간주
                item_path = path / item
                if "." in item: # 파일
                    if not item_path.exists():
                        item_path.touch()
                        print(f"  └─ 📄 파일 생성: {item}")
                else: # 폴더
                    item_path.mkdir(exist_ok=True)
                    print(f"  └─ 📂 하위 폴더: {item}")

def create_initial_env():
    """환경변수 파일 껍데기 생성"""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        content = """# Google API Key
GEMINI_API_KEY=
GEMINI_KEY_PLANNING=

# OpenAI API Key (Optional)
OPENAI_API_KEY=
"""
        env_path.write_text(content, encoding="utf-8")
        print("🔑 .env 파일 생성 완료 (키를 입력하세요)")

def main():
    print(f"🚀 [System Setup] 2026 AI Novel Factory 인프라 구축 시작...\n")
    
    create_initial_env()
    create_structure(BASE_DIR, STRUCTURE)
    
    # 루트 레벨 필수 파일
    root_files = ["app.py", "model_selector.py", "system_utils.py", "requirements.txt"]
    for f in root_files:
        if not (BASE_DIR / f).exists():
            (BASE_DIR / f).touch()
            print(f"📦 루트 파일 생성: {f}")

    print("\n🎉 [Complete] 공장 뼈대 구축 완료!")
    print("👉 이제 각 폴더의 .py 파일에 실제 로직 코드를 붙여넣으세요.")
    print("👉 프롬프트 내용은 '00_기준정보_보물창고/99_지능형_프롬프트'의 .md 파일에 직접 작성하면 됩니다.")

if __name__ == "__main__":
    main()