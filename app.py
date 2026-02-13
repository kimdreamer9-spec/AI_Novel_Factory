import sys
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# 1. 환경변수 로드 (가장 먼저!)
load_dotenv() 

# 2. 루트 경로 확정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR

# 3. 필수 하위 부서 경로 등록
sub_dirs = ["03_전략기획실_Planning", "05_제작_스튜디오_Production", "02_분석실_Analysis", "06_품질관리_QC", "00_기준정보_보물창고"]
for d in sub_dirs:
    p = PROJECT_ROOT / d
    if str(p) not in sys.path: sys.path.append(str(p))

st.set_page_config(page_title="AI Novel Factory CEO", page_icon="🏭", layout="wide")

# CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 4px 4px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 2px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🏭 Factory Control")
    
    # 키 체크
    key = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
    if key: st.success("✅ API Key Loaded")
    else: st.error("❌ API Key Missing")
    
    try:
        import model_selector
        st.info(f"🚀 Engine: **{model_selector.find_best_model()}**")
    except: st.error("Engine Error")
        
    st.divider()
    st.caption("v2026.2.3 (Final)")

st.title("AI Novel Factory : CEO Dashboard")

tabs = st.tabs(["🧠 전략기획실", "🗂️ 기획창고", "✍️ 제작스튜디오", "⚖️ 품질관리"])

with tabs[0]:
    try:
        import ui_planning
        ui_planning.render()
    except Exception as e: st.error(f"기획실 오류: {e}")

with tabs[1]:
    try:
        import ui_warehouse
        ui_warehouse.render(PROJECT_ROOT / "03_전략기획실_Planning")
    except Exception as e: st.error(f"창고 오류: {e}")

with tabs[2]:
    try:
        import ui_production
        ui_production.render(PROJECT_ROOT / "03_전략기획실_Planning", PROJECT_ROOT / "05_제작_스튜디오_Production")
    except Exception as e: st.error(f"제작소 오류: {e}")

with tabs[3]:
    st.info("🚧 공사 중")