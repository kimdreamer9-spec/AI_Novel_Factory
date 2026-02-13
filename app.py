import sys
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# =========================================================
# 🏗️ [System Setup] 절대 경로 및 환경 설정 (가장 먼저 실행)
# =========================================================

# 1. 루트 경로 확정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR

# 2. 필수 하위 부서 경로 등록 (sys.path)
# 이 코드가 없으면 하위 폴더의 모듈을 import 할 수 없음
sub_dirs = [
    PROJECT_ROOT / "03_전략기획실_Planning",
    PROJECT_ROOT / "05_제작_스튜디오_Production",
    PROJECT_ROOT / "02_분석실_Analysis",
    PROJECT_ROOT / "06_품질관리_QC",
    PROJECT_ROOT / "00_기준정보_보물창고"
]

for p in sub_dirs:
    if str(p) not in sys.path:
        sys.path.append(str(p))

# 3. 환경변수 로드 (.env)
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# =========================================================
# 🎨 [UI Config] 스트림릿 페이지 설정
# =========================================================
st.set_page_config(
    page_title="AI Novel Factory CEO Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (가독성 향상)
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 2px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🎛️ [Sidebar] 글로벌 컨트롤 타워
# =========================================================
with st.sidebar:
    st.header("🏭 Factory Control")
    
    # 1. API 상태 점검
    api_key_status = "✅ 연결됨" if os.getenv("GEMINI_API_KEY") else "❌ 키 없음"
    st.caption(f"Gemini API: {api_key_status}")
    
    # 2. 모델 상태 점검
    try:
        import model_selector
        best_model = model_selector.find_best_model()
        st.success(f"🚀 Active Engine:\n{best_model}")
    except Exception as e:
        st.error(f"⚠️ 엔진 오류: {e}")
        
    st.divider()
    st.markdown("### 📂 바로가기")
    st.page_link("app.py", label="메인 대시보드", icon="🏠")
    st.caption("v2026.2.0 (Ultimate)")

# =========================================================
# 🚀 [Main Content] 부서별 탭 렌더링
# =========================================================
st.title("AI Novel Factory : CEO Dashboard")
st.markdown("**기획(Planning)** ➔ **저장(Warehouse)** ➔ **제작(Production)** ➔ **검수(QC)**")

# 탭 구성
tabs = st.tabs([
    "🧠 1. 전략기획실", 
    "🗂️ 2. 기획창고", 
    "✍️ 3. 제작스튜디오", 
    "⚖️ 4. 품질관리"
])

# --- Tab 1: 전략기획실 (Planning) ---
with tabs[0]:
    try:
        import ui_planning
        ui_planning.render()
    except ImportError:
        st.error("🚨 `ui_planning.py`를 찾을 수 없습니다. `03_전략기획실_Planning` 폴더를 확인하세요.")
    except Exception as e:
        st.error(f"💥 기획실 시스템 붕괴: {e}")

# --- Tab 2: 기획창고 (Warehouse) ---
with tabs[1]:
    try:
        import ui_warehouse
        # 창고 모듈에는 기획실 경로를 인자로 넘겨줘야 함
        ui_warehouse.render(PROJECT_ROOT / "03_전략기획실_Planning")
    except ImportError:
        st.warning("🚧 기획창고 모듈(`ui_warehouse.py`)이 아직 없습니다.")
    except Exception as e:
        st.error(f"💥 창고 시스템 오류: {e}")

# --- Tab 3: 제작스튜디오 (Production) ---
with tabs[2]:
    try:
        import ui_production
        # 제작소에는 기획 폴더와 결과물 폴더 경로가 필요
        ui_production.render(
            PROJECT_ROOT / "03_전략기획실_Planning",
            PROJECT_ROOT / "05_제작_스튜디오_Production"
        )
    except ImportError:
        st.warning("🚧 제작소 모듈(`ui_production.py`)이 아직 없습니다.")
    except Exception as e:
        st.error(f"💥 제작소 시스템 오류: {e}")

# --- Tab 4: 품질관리 (QC) ---
with tabs[3]:
    st.info("🚧 품질관리(QC) 부서는 현재 인테리어 공사 중입니다.")