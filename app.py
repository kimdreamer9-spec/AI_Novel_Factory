import streamlit as st
import sys
import time
import json
import os
import shutil
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V7 (Planning Warehouse & Multi-Tasking)
# =========================================================

# 1. 경로 설정
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production" # 실제 제작 폴더 (가정)
sys.path.append(str(planning_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 엔진 로드
try:
    import strategy_judge as engine
    engine.init_engine()
    ENGINE_STATUS = "🟢 엔진 정상"
    MODEL_INFO = getattr(engine, 'MODEL_NAME', 'Unknown')
except ImportError:
    ENGINE_STATUS = "🔴 엔진 연결 실패"
    MODEL_INFO = "Unknown"

# 3. Helper Functions
def load_project_data(folder_path):
    json_path = folder_path / "Approved_Plan.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def move_to_production(project_name):
    # 기획 폴더에서 제작 상태(Status)를 변경하거나 마킹
    # 여기서는 간단히 session_state에 'active_projects'로 관리 (실제로는 DB나 파일에 state 저장 권장)
    if 'active_projects' not in st.session_state:
        st.session_state.active_projects = []
    if project_name not in st.session_state.active_projects:
        st.session_state.active_projects.append(project_name)
    return True

def delete_project(folder_path):
    try:
        shutil.rmtree(folder_path)
        return True
    except Exception as e:
        return False

# 4. 헤더
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 탭 구성 (4개로 확장)
tab_plan, tab_warehouse, tab_production, tab_qc = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소(가동중)", "⚖️ 4. 품질관리"])

# =========================================================
# 💡 1. 기획실 (Strategy Room) - 생산 위주
# =========================================================
with tab_plan:
    st.subheader("🧠 신규 기획 생성")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode_idx = st.radio("모드 선택", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        user_input = st.text_area("키워드 / 아이디어", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            with st.spinner("PD가 기획 중..."):
                mode_num = int(mode_idx[0])
                res, logs = engine.process_planning(mode_num, user_input)
                st.session_state.current_plan = res
                st.rerun()

    with c2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            st.markdown(f"## 📑 {plan.get('title')}")
            st.info(f"로그라인: {plan.get('logline')}")
            
            with st.expander("상세 내용 보기"):
                st.write(plan.get('synopsis'))
                st.json(plan.get('characters'))
            
            # 결재 버튼 (저장만 함)
            if st.button("💾 기획안 저장 (창고로 보내기)"):
                success, msg = engine.save_and_deploy(plan) # 일단 파일로 저장
                if success:
                    st.toast("기획 창고에 입고되었습니다!", icon="📦")
                    st.success(msg)
                    st.session_state.current_plan = None # 초기화
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
            
            # (반려/폐기 버튼 생략)

# =========================================================
# 🗂️ 2. 기획 창고 (Warehouse) - 물류 관리
# =========================================================
with tab_warehouse:
    st.subheader("📦 기획안 보관소 (Project Archive)")
    st.caption("저장된 기획안을 검토하고, 제작소로 투입하거나 폐기합니다.")

    # 폴더 스캔
    try:
        all_projects = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith("__") and not f.name.startswith(".")]
        all_projects.sort(key=lambda x: x.stat().st_mtime, reverse=True) # 최신순
    except: all_projects = []

    if not all_projects:
        st.warning("보관된 기획안이 없습니다.")
    else:
        for proj_dir in all_projects:
            data = load_project_data(proj_dir)
            if not data: continue # 데이터 없으면 패스
            
            # 카드 UI
            with st.expander(f"📁 {data.get('title')} ({proj_dir.name})"):
                c_info, c_action = st.columns([3, 1])
                
                with c_info:
                    st.write(f"**장르:** {data.get('genre')} | **로그라인:** {data.get('logline')}")
                    st.caption(f"경로: {proj_dir}")
                
                with c_action:
                    # 제작 투입 버튼
                    is_active = proj_dir.name in st.session_state.active_projects
                    
                    if is_active:
                        st.success("✅ 제작 중")
                    else:
                        if st.button("🚀 제작 투입", key=f"deploy_{proj_dir.name}"):
                            move_to_production(proj_dir.name)
                            st.toast(f"'{data.get('title')}' 제작 라인 가동!", icon="🔥")
                            st.rerun()
                    
                    # 삭제 버튼
                    if st.button("🗑️ 영구 삭제", key=f"del_{proj_dir.name}"):
                        delete_project(proj_dir)
                        st.warning("삭제되었습니다.")
                        st.rerun()

# =========================================================
# ✍️ 3. 제작소 (Production) - 멀티태스킹 현황판
# =========================================================
with tab_production:
    st.subheader("🏭 실시간 제작 현황 (Multi-Tasking Dashboard)")
    
    active_list = st.session_state.active_projects
    
    if not active_list:
        st.info("현재 가동 중인 라인이 없습니다. [기획 창고]에서 작품을 투입해주세요.")
    else:
        # 탭으로 작품 구분 (멀티태스킹)
        proj_tabs = st.tabs([name.split('_')[-1][:10]+"..." for name in active_list])
        
        for i, proj_name in enumerate(active_list):
            with proj_tabs[i]:
                proj_path = planning_dir / proj_name
                data = load_project_data(proj_path)
                
                if not data:
                    st.error("데이터 로드 실패")
                    continue

                st.markdown(f"### 🎬 {data.get('title')}")
                
                # 진행 상황 (가짜 데이터 시뮬레이션)
                col_status, col_chat = st.columns([1, 2])
                
                with col_status:
                    st.info("📊 진행률")
                    st.progress(45) # 예시
                    st.write("현재 작업: **제 5화 - 던전의 붕괴** 집필 중...")
                    st.caption("예상 완료 시간: 15분 뒤")
                    
                    if st.button("⏹️ 제작 중단 (창고로 반환)", key=f"stop_{proj_name}"):
                        st.session_state.active_projects.remove(proj_name)
                        st.rerun()

                with col_chat:
                    st.write("💬 **집필 AI 지시**")
                    # 각 작품별 독립된 채팅창 필요 (여기선 간소화)
                    st.chat_message("assistant").write(f"'{data.get('title')}' 5화 초안 작성 중입니다. 수정 사항 있으신가요?")
                    st.chat_input(f"'{data.get('title')}'에 대한 지시 입력...", key=f"chat_{proj_name}")

# =========================================================
# ⚖️ 4. 품질관리 (QC)
# =========================================================
with tab_qc:
    st.info("QC팀 대기 중")