import sys
import os

# =========================================================
# 🚨 [사장님의 긴급 패치] 경로 강제 통합 (Path Fix)
# 시스템 라이브러리(Plotly)와 유저 라이브러리(Streamlit)를 강제로 연결
# =========================================================
paths_to_add = [
    "/usr/local/python/3.12.1/lib/python3.12/site-packages",  # Plotly가 숨어있는 곳
    "/home/codespace/.local/lib/python3.12/site-packages"     # Streamlit이 사는 곳
]

for p in paths_to_add:
    if p not in sys.path:
        sys.path.append(p)

# ---------------------------------------------------------
# 🏭 AI Novel Factory V22 (Path-Patched Version)
# ---------------------------------------------------------
import streamlit as st
from pathlib import Path

# 1. 페이지 설정
st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 경로 설정
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

sys.path.append(str(current_dir))
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir))

# 3. 모듈 로드 (안전 장치 포함)
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
    # Plotly 확인 사살 (이제 경로가 뚫려서 보여야 함)
    if not ui_warehouse.HAS_PLOTLY:
        st.toast("⚠️ 경로 패치에도 불구하고 Plotly를 찾지 못했습니다.", icon="❓")
    else:
        st.toast("✅ Plotly 경로 연결 성공! 육각형 그래프 가동.", icon="📈")
except ImportError as e:
    st.error(f"창고 로드 실패: {e}")

try: import ui_production
except ImportError as e: st.error(f"제작소 로드 실패: {e}")

# 4. 메인 UI
st.title("🏭 AI 소설 공장 통합 관제탑")

if model_selector:
    eng = model_selector.find_best_model()
    st.caption(f"🚀 Engine: {eng}")

# 5. 탭 구성
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