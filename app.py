import streamlit as st
import sys
import os
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V21 (Stable Version)
# =========================================================

# 1. 경로 설정 (가장 먼저 해야 함)
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

sys.path.append(str(current_dir))
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 모듈 로드 (안전 장치 포함)
try: import system_utils as utils
except ImportError: utils = None

try: import model_selector
except ImportError: model_selector = None

# UI 모듈 로드
ui_planning = None
ui_warehouse = None
ui_production = None

try: import ui_planning
except ImportError as e: st.error(f"기획실 로드 실패: {e}")

try: 
    import ui_warehouse
except ImportError as e:
    # 창고는 Plotly 없으면 내부적으로 처리하도록 수정했으므로, 여기서 에러나면 진짜 경로 문제임
    st.error(f"창고 로드 실패: {e}")

try: import ui_production
except ImportError as e: st.error(f"제작소 로드 실패: {e}")

# 3. 메인 UI
st.title("🏭 AI 소설 공장 통합 관제탑")

if model_selector:
    eng = model_selector.find_best_model()
    st.caption(f"🚀 Engine: {eng}")

# 4. 탭 구성
t1, t2, t3, t4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소", "⚖️ 4. 품질관리"])

# 세션 초기화
if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

with t1:
    if ui_planning: ui_planning.render()
with t2:
    if ui_warehouse: ui_warehouse.render(planning_dir)
with t3:
    if ui_production: ui_production.render(planning_dir, production_dir)
with t4:
    st.info("준비 중")