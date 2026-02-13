import sys
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# =========================================================
# 🏭 [Central Command] AI Novel Factory Main
# =========================================================

# 1. 경로 설정 (Path Safety)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR

# 필수 하위 폴더 연결
sub_dirs = [
    "00_기준정보_보물창고",
    "02_분석실_Analysis",
    "03_전략기획실_Planning",
    "05_제작_스튜디오_Production",
    "06_품질관리_QC"
]
for d in sub_dirs:
    p = PROJECT_ROOT / d
    if str(p) not in sys.path: sys.path.append(str(p))

# 2. 환경변수 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# 3. 페이지 기본 설정
st.set_page_config(
    page_title="AI Novel Factory : CEO Dashboard", 
    page_icon="🏭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# [CSS Styling] 탭 가독성 최적화
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #f8f9fa;
        border-radius: 5px 5px 0 0; border: 1px solid #e0e0e0; border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff; border-top: 3px solid #ff4b4b; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- [Sidebar] 시스템 상태창 ---
with st.sidebar:
    st.title("🏭 Factory Control")
    
    # API 키 상태 모니터링
    # .env 파일에서 키를 못 읽어오면 여기서 빨간불이 뜹니다.
    oa_key = os.getenv("OPENAI_API_KEY")
    gm_key = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY_WRITING")
    
    if gm_key: 
        st.success(f"Gemini API\nReady ({str(gm_key)[:5]}...)", icon="🟢")
    else: 
        st.error("Gemini API\n키 없음 (.env 확인)", icon="❌")

    st.divider()
    
    # 엔진 상태 확인
    try:
        import model_selector
        engine_name = model_selector.find_best_model()
        st.info(f"🚀 **Active Engine**\n\n`{engine_name}`")
    except:
        st.warning("⚠️ Engine Error")
        
    st.divider()
    st.caption("v2026.3.1 (Stable Fix)")

# --- [Main] 4대 부서 탭 ---
st.title("AI Novel Factory : CEO Dashboard")

# 세션 초기화
if "active_projects" not in st.session_state: st.session_state.active_projects = []
if "current_plan" not in st.session_state: st.session_state.current_plan = None

# 탭 구성 (에러 격리 처리 적용)
tab1, tab2, tab3, tab4 = st.tabs(["🧠 전략기획실", "🗂️ 기획창고", "✍️ 제작스튜디오", "⚖️ 품질관리"])

# 1. 기획실
with tab1:
    try:
        import ui_planning
        ui_planning.render()
    except Exception as e:
        st.error(f"🚨 기획실 로드 실패: {e}")

# 2. 창고
with tab2:
    try:
        import ui_warehouse
        ui_warehouse.render(PROJECT_ROOT / "03_전략기획실_Planning")
    except Exception as e:
        st.error(f"🚨 창고 로드 실패: {e}")

# 3. 제작소
with tab3:
    try:
        import ui_production
        ui_production.render(
            PROJECT_ROOT / "03_전략기획실_Planning", 
            PROJECT_ROOT / "05_제작_스튜디오_Production"
        )
    except Exception as e:
        st.error(f"🚨 제작소 로드 실패: {e}")

# 4. QC
with tab4:
    st.info("🚧 품질관리 부서는 확장 공사 중입니다.")