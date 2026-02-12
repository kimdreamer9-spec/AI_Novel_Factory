import streamlit as st
import sys
import os
from pathlib import Path

# =========================================================
# 🚑 AI Novel Factory V23 (Emergency Recovery Mode)
# =========================================================

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 1. 경로 강제 설정 (Path Fix)
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

# 시스템 경로에 추가
sys.path.append(str(current_dir))
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir))

# 2. 모듈 로드 (안전 장치: 하나가 터져도 나머지는 살린다)
try: import system_utils as utils
except: utils = None

try: import model_selector
except: model_selector = None

# UI 모듈 로드 (개별 try-except)
ui_planning = None
try: import ui_planning
except Exception as e: st.error(f"🚨 기획실 로드 실패: {e}")

ui_warehouse = None
try: import ui_warehouse
except Exception as e: st.error(f"🚨 창고 로드 실패: {e}")

ui_production = None
try: import ui_production
except Exception as e: st.error(f"🚨 제작소 로드 실패: {e}")

# 3. 메인 화면
st.title("🏭 AI 소설 공장 통합 관제탑 (복구 모드)")

if model_selector:
    try:
        eng = model_selector.find_best_model()
        st.caption(f"🚀 Engine: {eng}")
    except: st.caption("🚀 Engine: Unknown")

# 4. 탭 구성
t1, t2, t3, t4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소", "⚖️ 4. 품질관리"])

# 세션 초기화
if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 렌더링
with t1:
    if ui_planning: ui_planning.render()
    else: st.warning("기획실 모듈을 점검 중입니다.")

with t2:
    if ui_warehouse: ui_warehouse.render(planning_dir)
    else: st.warning("창고 모듈을 점검 중입니다.")

with t3:
    if ui_production: ui_production.render(planning_dir, production_dir)
    else: st.warning("제작소 모듈을 점검 중입니다.")

with t4:
    st.info("준비 중")