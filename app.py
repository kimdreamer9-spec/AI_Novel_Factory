import sys
import os
from pathlib import Path
import streamlit as st

# =========================================================
# 🏗️ [System Path Architecture] 경로 고속도로 개통
# =========================================================
# 1. 현재 위치 및 루트 경로 확정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir

# 2. 필수 부서 경로 설정
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"
analysis_dir = current_dir / "02_분석실_Analysis"
qc_dir = current_dir / "06_품질관리_QC"

# 3. 파이썬에게 경로 인식 시키기 (sys.path)
paths_to_add = [
    str(root_dir),
    str(planning_dir),
    str(production_dir),
    str(analysis_dir),
    str(qc_dir),
    # [Codespace/Cloud 환경 대응] 시스템 라이브러리 경로 강제 연결
    "/usr/local/python/3.12.1/lib/python3.12/site-packages",
    "/home/codespace/.local/lib/python3.12/site-packages"
]

for p in paths_to_add:
    if p not in sys.path:
        sys.path.append(p)

# =========================================================
# 🎨 [Front-End] AI Novel Factory CEO Dashboard
# =========================================================

st.set_page_config(
    page_title="AI 소설 공장 (CEO 관제탑)", 
    layout="wide", 
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# --- [사이드바] 글로벌 설정 ---
with st.sidebar:
    st.header("⚙️ 시스템 제어")
    
    # 모델 상태 확인
    try:
        import model_selector
        eng = model_selector.find_best_model()
        st.success(f"🚀 엔진: {eng}")
    except:
        st.error("⚠️ 모델 셀렉터 연결 실패")

    st.divider()
    st.info("💡 **Tip**: 기획실에서 '기획 엔진'을 가동하면 창고에 자동 저장됩니다.")
    st.markdown("---")
    st.caption("v24.0.0 (Ultimate Build)")

# --- [메인] 타이틀 및 탭 구성 ---
st.title("🏭 AI 소설 공장 통합 관제탑")
st.markdown("##### **[Planning]** ➔ **[Storage]** ➔ **[Production]** Pipeline")

# 4개의 핵심 부서 탭
t1, t2, t3, t4 = st.tabs([
    "🧠 1. 전략기획실 (Planning)", 
    "🗂️ 2. 기획창고 (Warehouse)", 
    "✍️ 3. 제작 스튜디오 (Production)", 
    "⚖️ 4. 품질관리 (QC)"
])

# =========================================================
# 🧩 [Module Connector] 각 부서 모듈 연결 및 렌더링
# =========================================================

# 세션 초기화 (안전 장치)
if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# --- 1. 전략기획실 ---
with t1:
    try:
        import ui_planning
        ui_planning.render()
    except Exception as e:
        st.error(f"🚨 기획실 모듈 로드 실패: {e}")
        st.info("📌 확인: `03_전략기획실_Planning/ui_planning.py` 파일이 존재하는지 확인하세요.")

# --- 2. 기획창고 ---
with t2:
    try:
        import ui_warehouse
        # ui_warehouse가 제대로 경로를 받을 수 있게 인자 전달
        ui_warehouse.render(planning_dir)
    except Exception as e:
        st.error(f"🚨 창고 모듈 로드 실패: {e}")
        # Plotly 문제일 경우 힌트 제공
        if "plotly" in str(e):
            st.warning("📉 시각화 도구(Plotly)가 설치되지 않았거나 경로 문제일 수 있습니다.")

# --- 3. 제작 스튜디오 ---
with t3:
    try:
        import ui_production
        # 기획안 폴더와 결과물 폴더를 인자로 전달
        ui_production.render(planning_dir, production_dir)
    except Exception as e:
        st.error(f"🚨 제작소 모듈 로드 실패: {e}")

# --- 4. 품질관리 ---
with t4:
    st.info("🚧 품질관리(QC) 부서는 현재 채용 중입니다. (추후 업데이트)")
    # 추후 ui_qc.render() 연결 예정