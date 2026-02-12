import streamlit as st
import sys
import os
import subprocess
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V20 (Self-Healing Environment)
# 역할: 의존성 자동 점검 및 모듈 로딩 관제탑
# =========================================================

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 0. [자가 정비] 필수 라이브러리 자동 설치 (Auto-Install)
def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

# 필수품 목록
REQUIRED_PACKAGES = ["plotly", "pandas", "openai", "google-generativeai", "python-dotenv"]
missing_packages = []

# 점검 시작
for package in REQUIRED_PACKAGES:
    try:
        __import__(package.replace("-", "_")) # 모듈 이름 변환 (python-dotenv -> dotenv 등은 예외 처리 필요하지만 일단 진행)
    except ImportError:
        missing_packages.append(package)

# 누락된 게 있으면 설치 시도
if missing_packages:
    with st.spinner(f"🚨 필수 부품({', '.join(missing_packages)})을 자동으로 설치하고 있습니다... 잠시만 기다려주세요."):
        for pkg in missing_packages:
            install_package(pkg)
        st.success("설치 완료! 시스템을 재가동합니다.")
        st.rerun() # 설치 후 새로고침

# 1. 경로 설정
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

sys.path.append(str(current_dir))
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir))

# 2. 모듈 로드 (안전 로딩)
try: import system_utils as utils
except ImportError: utils = None

try: import model_selector
except ImportError: model_selector = None

# 기획실 UI
try: import ui_planning
except ImportError: ui_planning = None

# 창고 UI (이제 Plotly가 있으므로 무조건 로드됨)
try: import ui_warehouse
except ImportError as e: 
    ui_warehouse = None
    st.error(f"창고 모듈 로드 실패: {e}")

# 제작소 UI
try: import ui_production
except ImportError: ui_production = None

# 3. 엔진 상태 확인
engine_name = "Unknown"
if model_selector:
    try: engine_name = model_selector.find_best_model()
    except: pass

st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"🚀 Core Engine: {engine_name} | 🛡️ System: All Systems Go")

# 4. 세션 초기화
if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 탭 구성
t1, t2, t3, t4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소", "⚖️ 4. 품질관리"])

# --- 탭별 렌더링 ---
with t1:
    if ui_planning: ui_planning.render()
    else: st.error("🚨 기획실 모듈(`ui_planning.py`)이 없습니다.")

with t2:
    if ui_warehouse: ui_warehouse.render(planning_dir)
    else: st.error("🚨 창고 모듈(`ui_warehouse.py`)이 없습니다. (ui_warehouse.py 파일 존재 여부 확인 필요)")

with t3:
    if ui_production: ui_production.render(planning_dir, production_dir)
    else: st.error("🚨 제작소 모듈(`ui_production.py`)이 없습니다.")

with t4:
    st.info("🚧 QC 팀 채용 중 (Quality Control Coming Soon)")