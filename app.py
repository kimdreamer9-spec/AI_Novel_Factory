import streamlit as st
import sys
import os
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V19 (Independent Module Loading)
# =========================================================

# 1. 경로 설정
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

sys.path.append(str(current_dir))
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 개별 모듈 로드 (연쇄 폭발 방지)
# (1) 시스템 유틸
try: import system_utils as utils
except ImportError: utils = None

# (2) 모델 셀렉터
try: import model_selector
except ImportError: model_selector = None

# (3) 기획실 UI
try: import ui_planning
except ImportError as e: 
    ui_planning = None
    st.toast(f"기획실 로드 실패: {e}", icon="⚠️")

# (4) 창고 UI (여기가 터져도 기획실은 살아야 함)
try: import ui_warehouse
except ImportError as e: 
    ui_warehouse = None
    # Plotly 에러일 경우 명확히 알려줌
    if "plotly" in str(e):
        st.toast("창고 로드 실패: plotly 모듈이 없습니다.", icon="📉")
    else:
        st.toast(f"창고 로드 실패: {e}", icon="⚠️")

# (5) 제작소 UI
try: import ui_production
except ImportError as e: 
    ui_production = None
    st.toast(f"제작소 로드 실패: {e}", icon="⚠️")

# 3. 상태 메시지 결정
engine_name = "Unknown"
if model_selector:
    try: engine_name = model_selector.find_best_model()
    except: pass

st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"🚀 Core Engine: {engine_name}")

# 4. 세션 초기화
if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 탭 구성
t1, t2, t3, t4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소", "⚖️ 4. 품질관리"])

# --- 탭별 렌더링 (안전하게) ---
with t1:
    if ui_planning: ui_planning.render()
    else: st.error("🚨 기획실 모듈(`ui_planning.py`)이 없습니다.")

with t2:
    if ui_warehouse: ui_warehouse.render(planning_dir)
    else: 
        st.error("🚨 창고 모듈(`ui_warehouse.py`)이 없습니다.")
        if not utils: st.warning("system_utils도 없습니다.")
        st.info("💡 힌트: `pip install plotly pandas`를 하셨나요?")

with t3:
    if ui_production: ui_production.render(planning_dir, production_dir)
    else: st.error("🚨 제작소 모듈(`ui_production.py`)이 없습니다.")

with t4:
    st.info("🚧 QC 팀 채용 중")