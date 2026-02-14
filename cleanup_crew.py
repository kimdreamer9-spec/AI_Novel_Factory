import os
import shutil
from pathlib import Path

# =========================================================
# 🧹 [청소반장] Cleanup Crew (Auto-Organizer)
# 역할: 공장 내부의 중복 파일을 제거하고, 도구를 공구함으로 이동시킵니다.
# =========================================================

BASE_DIR = Path.cwd()

def log(msg):
    print(f"✨ {msg}")

def move_file(src, dst_folder):
    """파일을 안전하게 이동 (없으면 패스)"""
    if src.exists():
        dst = dst_folder / src.name
        if dst.exists():
            log(f"[중복삭제] {src.name}이(가) 이미 {dst_folder.name}에 있어 삭제합니다.")
            src.unlink()
        else:
            shutil.move(str(src), str(dst))
            log(f"[이동] {src.name} -> {dst_folder.name}")

def delete_file(src):
    """파일 삭제"""
    if src.exists():
        src.unlink()
        log(f"[삭제] {src.name} 제거 완료")

def main():
    log("🧹 공장 내부 대청소를 시작합니다...")

    # 1. [시스템 도구함] 생성
    tools_dir = BASE_DIR / "99_시스템_도구함"
    tools_dir.mkdir(exist_ok=True)
    log("📂 '99_시스템_도구함' 폴더 생성 완료")

    # 2. 너저분한 루트 파일들 -> 도구함으로 이동
    files_to_move = [
        "check_api_status.py", 
        "check_models.py", 
        "drive_connector.py",
        "scanner_pro.py",
        "text_importer.py",
        "processor_pro.py"  # 루트에 있다면 이동
    ]
    
    for f in files_to_move:
        move_file(BASE_DIR / f, tools_dir)

    # 3. [중복 제거] 01_자료실 내부의 파이썬 파일 박멸
    raw_data_dir = BASE_DIR / "01_자료실_Raw_Data"
    if raw_data_dir.exists():
        # 자료실 루트에 있는 processor_pro.py 등 이동
        move_file(raw_data_dir / "processor_pro.py", tools_dir)
        move_file(raw_data_dir / "scanner_pro.py", tools_dir)
        move_file(raw_data_dir / "text_importer.py", tools_dir)
        
        # 하위 폴더(투입구)에 잘못 들어간 파일 삭제
        delete_file(raw_data_dir / "99_이미지_투입구" / "processor_pro.py")
        delete_file(raw_data_dir / "99_텍스트_투입구" / "processor_pro.py")

    # 4. [분석실 통합] staff, leader 삭제 -> master만 남기기
    analysis_dir = BASE_DIR / "02_분석실_Analysis"
    if analysis_dir.exists():
        delete_file(analysis_dir / "staff_analyst.py")
        delete_file(analysis_dir / "leader_analyst.py")
        log("[통합] staff/leader 분석가 해고 (Master Analyst로 통합 예정)")

    # 5. [방어막 설치] .gitignore 자동 생성
    gitignore_path = BASE_DIR / ".gitignore"
    gitignore_content = """
# 1. 시스템 파일 무시
venv/
__pycache__/
.env
.DS_Store

# 2. 대용량 자료실 무시 (깃허브 용량 초과 방지)
01_자료실_Raw_Data/*

# 3. 예외: 성공작 아카이브(결과물)는 업로드 허용
!01_자료실_Raw_Data/00_성공작_아카이브/

# 4. 예외: 투입구 폴더 자체는 유지 (.gitkeep)
!01_자료실_Raw_Data/99_이미지_투입구/
!01_자료실_Raw_Data/99_텍스트_투입구/
"""
    gitignore_path.write_text(gitignore_content, encoding='utf-8')
    log("🛡️ .gitignore 파일 최신화 완료 (이미지 폭탄 방지)")

    print("\n🎉 [청소 끝] 공장이 말끔해졌습니다!")
    print(f"👉 이제 도구들은 '{tools_dir.name}'에 모여 있습니다.")

if __name__ == "__main__":
    main()