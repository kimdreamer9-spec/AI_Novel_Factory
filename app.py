import streamlit as st
import sys
import os
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V18 (The Clean Frontend)
# 역할: 중앙 관제탑 (UI Only) - API 호출은 각 부서(모듈)에 위임
# =========================================================

# 1. 경로 설정 (각 부서 위치 등록)
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

sys.path.append(str(current_dir))
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir))

# 2. 페이지 설정
st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 3. 모듈 로드 (부서장 호출)
# 주의: 여기서 에러가 나면 해당 폴더의 파일명이나 코드를 확인해야 함
try:
    import system_utils as utils      # 행정실
    import model_selector             # 인사과 (모델 확인용)
    import ui_planning                # 기획실 UI
    import ui_warehouse               # 창고 UI
    import ui_production              # 제작소 UI
    
    # 현재 가동 중인 최강 모델 확인 (인사과에 문의)
    try:
        CORE_ENGINE = model_selector.find_best_model()
        STATUS_MSG = f"🟢 시스템 정상 | 🔥 Core Engine: {CORE_ENGINE}"
    except:
        STATUS_MSG = "🟡 모델 셀렉터 응답 없음 (기본 모델 가동)"

except ImportError as e:
    STATUS_MSG = f"🔴 모듈 로드 실패: {e}"
    # UI가 뻗지 않도록 빈 껍데기 변수 처리 (안전장치)
    ui_planning = ui_warehouse = ui_production = None

# 4. 세션 상태 초기화 (메모리)
if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# =========================================================
# 🖥️ Main UI (Dashboard)
# =========================================================

# 헤더
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(STATUS_MSG)

# 탭 구성 (부서 이동)
tab1, tab2, tab3, tab4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소", "⚖️ 4. 품질관리"])

# --- 1. 기획실 (Strategy Room) ---
with tab1:
    if ui_planning:
        ui_planning.render()
    else:
        st.error("🚨 기획실 모듈(`ui_planning.py`)을 불러오지 못했습니다.")

# --- 2. 기획 창고 (Warehouse) ---
with tab2:
    if ui_warehouse:
        ui_warehouse.render(planning_dir)
    else:
        st.error("🚨 창고 모듈(`ui_warehouse.py`)을 불러오지 못했습니다.")

# --- 3. 제작소 (Production Studio) ---
with tab3:
    if ui_production:
        ui_production.render(planning_dir, production_dir)
    else:
        st.error("🚨 제작소 모듈(`ui_production.py`)을 불러오지 못했습니다.")

# --- 4. 품질관리 (QC) ---
with tab4:
    st.info("🚧 QC 팀은 현재 채용 중입니다. (다음 업데이트 예정)")