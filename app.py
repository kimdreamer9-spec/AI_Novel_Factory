import streamlit as st
import sys
import os
import json
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 🏗️ [Setup] 경로 및 환경 설정 (Path Safety)
# =========================================================
CURRENT_FILE_PATH = Path(__file__).resolve()
PRODUCTION_DIR = CURRENT_FILE_PATH.parent          # 05_제작_스튜디오_Production
PROJECT_ROOT = PRODUCTION_DIR.parent               # Root

# 시스템 경로 추가 (모듈 로드용)
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
if str(PRODUCTION_DIR) not in sys.path: sys.path.append(str(PRODUCTION_DIR))

# 환경변수 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_WRITING") or os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 🤖 [AI Engine] 모델 셀렉터 연동
try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
except:
    MODEL_NAME = "gemini-1.5-flash" # Fallback

if API_KEY: genai.configure(api_key=API_KEY)

# =========================================================
# 🛠️ [Helper Functions] 기능 모듈
# =========================================================

def load_project_data(planning_dir, project_name):
    """기획안(plan.json)을 로드하여 집필 참고자료로 씁니다."""
    try:
        # 폴더명 매칭 (타임스탬프 등으로 인해 정확한 이름 찾기)
        target_dir = None
        for item in planning_dir.iterdir():
            if item.is_dir() and item.name == project_name:
                target_dir = item
                break
        
        if not target_dir: return None

        json_path = target_dir / "plan.json" # V48 이후 plan.json으로 저장됨
        
        # 구버전 호환 (metadata.json 등)
        if not json_path.exists():
            json_path = list(target_dir.glob("*.json"))[0]

        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def ai_write(prompt, context):
    """AI 작가에게 집필을 명령합니다."""
    full_prompt = f"""
    You are a **Top Web Novel Writer**.
    Write the next scene based on the context.
    
    [Context Info]
    - Title: {context.get('title')}
    - Genre: {context.get('genre')}
    - Characters: {str(context.get('characters', []))[:500]}
    
    [Instruction]
    {prompt}
    
    [Output Rule]
    - Language: Korean (Web novel style).
    - Format: Plain Text (Story content only).
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        res = model.generate_content(full_prompt)
        return res.text
    except Exception as e:
        return f"🚫 [AI Error] {str(e)}"

# =========================================================
# 🎨 [UI Render] 메인 화면
# =========================================================

def render(planning_dir, production_output_dir):
    st.markdown("## ✍️ 제작 스튜디오 (Production Studio)")
    st.caption(f"🚀 AI Writer Engine: **{MODEL_NAME}** | 🏭 Active Slots: 10")

    # 1. [Slot] 작업 중인 프로젝트 선택
    if "active_projects" not in st.session_state or not st.session_state.active_projects:
        st.warning("📭 현재 제작소에 투입된 작품이 없습니다.")
        st.info("💡 **[기획 창고]** 탭에서 '제작 투입' 버튼을 눌러 프로젝트를 가져오세요.")
        return

    selected_proj_name = st.selectbox("📂 작업할 프로젝트 선택 (Active Slot)", st.session_state.active_projects)
    
    # 2. 기획안 데이터 로드
    plan_data = load_project_data(planning_dir, selected_proj_name)
    if not plan_data:
        st.error("❌ 기획안 데이터를 불러올 수 없습니다. (파일 손상 또는 경로 오류)")
        return

    st.divider()

    # 3. [Dual View] 좌측: 설정집 / 우측: 집필실
    col_ref, col_writer = st.columns([1, 2])

    # --- [Left] Reference (설정 자료) ---
    with col_ref:
        with st.container(border=True):
            st.markdown("### 📚 설정 자료집")
            
            # A. 로그라인 & 의도
            with st.expander("📌 기획 의도", expanded=True):
                st.info(plan_data.get('logline', '로그라인 없음'))
                st.caption(plan_data.get('planning_intent', '-'))

            # B. 캐릭터 (카드 형태)
            with st.expander("👥 캐릭터 사전"):
                for char in plan_data.get('characters', []):
                    st.markdown(f"**{char.get('name')}** ({char.get('role')})")
                    st.caption(char.get('desc'))
                    st.markdown("---")

            # C. 세계관
            with st.expander("🌍 세계관 & 규칙"):
                st.write(plan_data.get('world_view', '설정 없음'))

            # D. 플롯
            with st.expander("🗺️ 회차별 플롯"):
                for p in plan_data.get('episode_plots', []):
                    st.markdown(f"**[{p.get('ep')}화]** {p.get('title')}")
                    st.caption(p.get('summary'))

    # --- [Right] Writer (집필 공간) ---
    with col_writer:
        st.markdown(f"### 📝 **{plan_data.get('title')}** - 집필 모드")
        
        # 회차 선택
        ep_num = st.number_input("Episode No.", min_value=1, value=1, format="%d화")
        
        # 입력 방식 (AI 지시 vs 직접 쓰기)
        tab_ai, tab_manual = st.tabs(["🤖 AI 작가 지시", "⌨️ 직접 쓰기"])
        
        with tab_ai:
            st.info("💡 AI에게 장면을 묘사하거나 대사를 쓰라고 지시하세요.")
            user_inst = st.text_area("지시사항 (Prompt)", height=100, placeholder="예: 주인공이 빌런을 처음 마주치고 비릿하게 웃는 장면을 묘사해줘.")
            
            if st.button("✨ 집필 시작 (Generate)", type="primary"):
                if not user_inst:
                    st.warning("지시사항을 입력하세요.")
                else:
                    with st.spinner("✍️ AI 작가가 원고를 작성 중입니다..."):
                        # 기획안 컨텍스트 주입
                        result_text = ai_write(user_inst, plan_data)
                        st.session_state[f"draft_{selected_proj_name}_{ep_num}"] = result_text
                        st.success("작성 완료!")

        # 결과물 에디터 (수정 가능)
        draft_key = f"draft_{selected_proj_name}_{ep_num}"
        current_draft = st.session_state.get(draft_key, "")
        
        final_draft = st.text_area("📄 원고 에디터 (Result)", value=current_draft, height=500)
        
        # 저장 버튼
        c1, c2 = st.columns([1, 4])
        if c1.button("💾 저장"):
            # 저장 로직 (파일 시스템에 저장)
            save_dir = production_output_dir / selected_proj_name
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / f"ep_{ep_num:03d}.txt"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_draft)
            
            st.toast(f"{ep_num}화 저장 완료!", icon="💾")