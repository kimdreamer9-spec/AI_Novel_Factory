import os
from pathlib import Path

# =========================================================
# 🏭 [AI 소설 공장] 최종 건설 스크립트 (Architect_Final_v3)
# 역할: 2026년형 하이브리드 생산 라인 및 데이터베이스 구축
# 포함: 사장님의 보물창고(작법서) 자동 생성 기능 탑재
# =========================================================

BASE_DIR = Path.cwd()

# 1. 디렉토리 및 파일 구조 정의
STRUCTURE = {
    "00_기준정보_보물창고": {
        "files": ["standard-rubric.json", "rubric_maker.py"],
        "subdirs": {
            "작법_이론서": [ # 사장님이 주신 팁들이 여기에 자동 생성됨
                "PD_작법서_요약.txt", 
                "유튜브_대사_필승공식.txt",
                "웹소설_기승전결_구조.txt"
            ]
        }
    },
    "01_자료실_Raw_Data": {
        "files": ["processor_pro.py", "text_importer.py", "scanner_pro.py"],
        "subdirs": {
            "99_이미지_투입구": [],     # (Action) 183개 스캔본 넣는 곳
            "99_텍스트_투입구": [],     # (Action) 기존 텍스트 파일 넣는 곳
            "00_성공작_아카이브": []    # (Result) 가공된 3박자 세트 저장소
        }
    },
    "02_분석실_Analysis": {
        "files": ["staff_analyst.py", "leader_analyst.py"]
    },
    "03_전략기획실_Planning": {
        "files": ["creative_planner.py", "red_team_plan.py", "strategy_judge.py"]
    },
    "04_설정_자료집": { # [NEW] 사장님의 고증 자료 저장소
        "files": [],
        "subdirs": {
            "A_대체역사_1800_2000": [ # (1873~1950 자료 등)
                "역사_연표_미국.txt", "무기_개발_연표.txt", "발명품_목록.txt", "인재_목록.txt"
            ],
            "B_현대판타지_1950_2026": [ # (현대물 필수 자료)
                "01_경제_역사", "02_기업_역사", "03_인물_DB", "04_꿀템_치트키"
            ],
            "C_공통_자료실": [
                "맛깔난_욕설모음.txt", "음식_묘사_사전.txt", "감정_표현_사전.txt"
            ]
        }
    },
    "05_제작_스튜디오_Production": {
        "files": [
            "01_treatment_writer.py", # (Gemini) 1화를 사건(Beat) 단위로 분할
            "02_character_bot.py",    # (DB) 캐릭터 붕괴 방지
            "03_main_writer.py",      # (Gemini 3.0) 릴레이 연쇄 집필 (글자수 무제한)
            "04_red_team_pd.py"       # (OpenAI) 실시간 감시 및 태클
        ]
    },
    "06_품질관리_QC": {
        "files": ["plagiarism_scanner.py", "final_polisher.py"]
    }
}

# 2. 자동 생성될 작법서 내용 (사장님이 주신 자료 요약)
TIPS_CONTENT = {
    "PD_작법서_요약.txt": """[PD 출신 작가의 웹소설 작법서 핵심]
1. 장르와 세계관: 장르는 A컷(웹툰)이자 배경 묘사(웹소설)다.
   - 판타지: 위협적인 대상을 올려다보는 주인공 (압도감)
   - 무협: 현란한 칼싸움, 복부에 칼이 박히는 직관적 묘사
2. 인간의 욕구 건드리기: 대리만족, 사이다, 갑질, 복수.
3. 돈과 죽음 이용하기:
   - 돈: 구체적인 액수, 벼락부자의 쾌감.
   - 죽음: 긴장감 조성, 주인공의 위기 혹은 각성 계기.
4. 트리트먼트 심화: 시놉시스보다 구체적인 씬(Scene) 단위 설계.""",

    "유튜브_대사_필승공식.txt": """[웹소설 대사 쓰는 법 - 방구석 이작가]
1. 목적 없는 대사 금지: 인사, 날씨 등 영양가 없는 말 삭제.
2. 예측 불가능성: 독자가 예상하는 답변을 비틀어라. (거절 대신 엉뚱한 조건 제시)
3. 구어체 디테일: 조사 생략, 도치법 사용 ("밥 먹었냐?" O, "식사는 하셨습니까?" X)
4. 티키타카: 탁구공처럼 빠르게 오가는 짧은 호흡.
5. 지문 삭제: 누가 말하는지 알면 '말했다' 지문은 과감히 뺀다.""",
    
    "무기_개발_연표.txt": """(여기에 사장님이 주신 '무기 개발 연표' 파일 내용을 붙여넣으세요.)""",
    
    "발명품_목록.txt": """(여기에 사장님이 주신 '발명품 목록' 파일 내용을 붙여넣으세요.)"""
}

def create_structure(base, structure):
    for name, content in structure.items():
        path = base / name
        
        # 1. 폴더 생성 (이미 있으면 패스)
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            print(f"📂 폴더 생성: {name}")
            
            # 파일 생성
            if "files" in content:
                for file in content["files"]:
                    file_path = path / file
                    if not file_path.exists():
                        file_path.touch()
                        print(f"   └─ 📄 파일 생성: {file}")
            
            # 서브 폴더 재귀 호출
            if "subdirs" in content:
                create_structure(path, content["subdirs"])
                
        # 2. 리스트인 경우 (마지막 단계 파일들)
        elif isinstance(content, list):
            path.mkdir(parents=True, exist_ok=True)
            for file in content:
                file_path = path / file
                if not file_path.exists():
                    file_path.touch()
                    # 팁 파일이면 내용 채워넣기
                    if file in TIPS_CONTENT:
                        file_path.write_text(TIPS_CONTENT[file], encoding='utf-8')
                        print(f"   └─ 📝 [작법서 작성]: {file}")
                    else:
                        print(f"   └─ 📄 파일 생성: {file}")

def main():
    print(f"🚀 [공장 건설] '{BASE_DIR.name}' 부지에 2026년형 AI 소설 공장을 짓습니다...\n")
    
    # .env 체크
    if not (BASE_DIR / ".env").exists():
        (BASE_DIR / ".env").touch()
        print("🔑 .env 파일 생성 (API 키를 입력하세요!)")

    create_structure(BASE_DIR, STRUCTURE)
    
    # 현대판타지 섹터 폴더 강제 생성 (리스트 안의 문자열 폴더 처리)
    modern_path = BASE_DIR / "04_설정_자료집" / "B_현대판타지_1950_2026"
    for folder in ["01_경제_역사", "02_기업_역사", "03_인물_DB", "04_꿀템_치트키"]:
        (modern_path / folder).mkdir(exist_ok=True)

    print("\n🎉 [건설 완료] 모든 생산 라인이 구축되었습니다.")
    print("👉 [1단계] '01_자료실_Raw_Data/99_이미지_투입구'에 183개 스캔본을 넣으십시오.")
    print("👉 [2단계] '04_설정_자료집' 각 폴더에 사장님의 귀한 자료들을 넣어주십시오.")
    print("👉 [3단계] 준비되면 'processor_pro.py 코드를 줘'라고 명령하십시오.")

if __name__ == "__main__":
    main()