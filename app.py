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

# 기획 엔진 경로 추가
if str(planning_dir) not in sys.path:
    sys.path.append(str(planning_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 엔진 로드 (안전장치)
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
    """
    기획 데이터를 로드하는 통합 함수 (신형/구형 호환)
    """
    # 1. 신형 포맷 (Approved_Plan.json) 확인
    json_path = folder_path / "Approved_Plan.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass

    # 2. 구형 포맷 (기획안_Draft...json) 확인
    drafts = list(folder_path.glob("기획안_Draft*.json"))
    if drafts:
        try:
            # 가장 최신 파일 선택
            drafts.sort(key=lambda x: x.stat().st_mtime, reverse=True) 
            with open(drafts[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                # 구형 데이터 키 매핑 (호환성 확보)
                if '1_작품_기본_정보' in data:
                    flat_data = {}
                    info = data.get('1_작품_기본_정보', {})
                    flat_data['title'] = info.get('제목', folder_path.name)
                    flat_data['genre'] = info.get('장르', '미상')
                    flat_data['logline'] = data.get('3_작품_소개_로그라인', '로그라인 없음')
                    flat_data['synopsis'] = "구형 데이터입니다. 상세 내용은 파일을 확인하세요."
                    flat_data['characters'] = []
                    return flat_data
                return data
        except: pass
        
    # 3. 데이터 없음 (폴더만 있는 경우)
    return {"title": folder_path.name, "logline": "데이터 형식 호환 불가 (수동 확인 필요)", "genre": "미상"}

def move_to_production(project_name):
    """기획 창고 -> 제작소 투입 (상태 변경)"""
    if 'active_projects' not in st.session_state:
        st.session_state.active_projects = []
    if project_name not in st.session_state.active_projects:
        st.session_state.active_projects.append(project_name)
    return True

def delete_project(folder_path):
    """프로젝트 영구 삭제"""
    try:
        shutil.rmtree(folder_path)
        return True
    except Exception as e:
        return False

# 4. 헤더 및 세션 초기화
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 탭 구성 (4개로 확장)
tab_plan, tab_warehouse, tab_production, tab_qc = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소(가동중)", "⚖️ 4. 품질관리"])

# =========================================================
# 💡 1. 기획실 (Strategy Room)
# =========================================================
with tab_plan:
    st.subheader("🧠 신규 기획 생성")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode_idx = st.radio("모드 선택", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        user_input = st.text_area("키워드 / 아이디어 / 문제점", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "🔴" in ENGINE_STATUS:
                st.error("엔진 연결 실패")
            else:
                with st.spinner("PD가 기획 중..."):
                    mode_num = int(mode_idx[0])
                    res, logs = engine.process_planning(mode_num, user_input)
                    st.session_state.current_plan = res
                    st.rerun()

    with c2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            
            # 보고서 UI
            st.markdown(f"## 📑 {plan.get('title', '제목 미정')}")
            st.info(f"💡 **로그라인:** {plan.get('logline')}")
            
            # 리스크 리포트 (경고창)
            risk = plan.get('risk_report', {})
            if risk.get('detected'):
                st.error(f"🚨 경고: {risk.get('red_team_warning')}")
                st.info(f"💡 대안: {risk.get('alternative_suggestion')}")

            with st.expander("상세 내용 보기", expanded=True):
                st.write(f"**기획의도:** {plan.get('planning_intent')}")
                st.write(f"**시놉시스:** {plan.get('synopsis')}")
            
            # 결재 버튼
            col_save, col_fix = st.columns(2)
            if col_save.button("💾 기획안 승인 (창고로 입고)"):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("기획 창고에 입고되었습니다!", icon="📦")
                    st.success(msg)
                    st.session_state.current_plan = None
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
            
            # 반려 기능 (간소화)
            if col_fix.button("🗑️ 폐기 (초기화)"):
                st.session_state.current_plan = None
                st.rerun()

# =========================================================
# 🗂️ 2. 기획 창고 (Warehouse)
# =========================================================
with tab_warehouse:
    st.subheader("📦 기획안 보관소 (Project Archive)")
    st.caption("과거의 명작들과 신규 기획안이 모두 이곳에 모입니다.")

    # 폴더 스캔 (구형/신형 모두)
    try:
        all_projects = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith("__") and not f.name.startswith(".")]
        all_projects.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: all_projects = []

    if not all_projects:
        st.warning("보관된 기획안이 없습니다.")
    else:
        for proj_dir in all_projects:
            data = load_project_data(proj_dir)
            if not data: continue
            
            # 카드 UI
            with st.expander(f"📁 {data.get('title')} ({proj_dir.name})"):
                c_info, c_action = st.columns([3, 1])
                
                with c_info:
                    st.write(f"**장르:** {data.get('genre')} | **로그라인:** {data.get('logline')}")
                    st.caption(f"시스템 경로: {proj_dir.name}")
                
                with c_action:
                    # 제작 투입 여부 확인
                    is_active = proj_dir.name in st.session_state.active_projects
                    
                    if is_active:
                        st.success("✅ 제작 라인 가동 중")
                    else:
                        if st.button("🚀 제작 투입", key=f"deploy_{proj_dir.name}"):
                            move_to_production(proj_dir.name)
                            st.toast(f"'{data.get('title')}' 제작 라인 가동!", icon="🔥")
                            st.rerun()
                    
                    if st.button("🗑️ 영구 삭제", key=f"del_{proj_dir.name}"):
                        delete_project(proj_dir)
                        st.warning("삭제되었습니다.")
                        st.rerun()

# =========================================================
# ✍️ 3. 제작소 (Production)
# =========================================================
with tab_production:
    st.subheader("🏭 실시간 제작 현황 (Multi-Tasking Dashboard)")
    
    active_list = st.session_state.active_projects
    
    if not active_list:
        st.info("현재 가동 중인 라인이 없습니다. [기획 창고]에서 작품을 투입해주세요.")
    else:
        # 탭으로 작품 구분
        proj_tabs = st.tabs([name.split('_')[-1][:10]+"..." for name in active_list])
        
        for i, proj_name in enumerate(active_list):
            with proj_tabs[i]:
                proj_path = planning_dir / proj_name
                data = load_project_data(proj_path)
                
                if not data:
                    st.error("데이터 로드 실패")
                    continue

                st.markdown(f"### 🎬 {data.get('title')}")
                
                col_status, col_chat = st.columns([1, 2])
                
                with col_status:
                    st.info("📊 집필 진행 상황")
                    st.progress(10) 
                    st.write("현재 단계: **시놉시스 분석 및 1화 트리트먼트**")
                    
                    if st.button("⏹️ 제작 중단 (창고로 반환)", key=f"stop_{proj_name}"):
                        st.session_state.active_projects.remove(proj_name)
                        st.rerun()

                with col_chat:
                    st.write("💬 **집필 AI 지시 (Command Center)**")
                    st.chat_message("assistant").write(f"'{data.get('title')}' 집필 준비 완료. 1화 작성을 시작할까요?")
                    st.chat_input(f"'{data.get('title')}'에 대한 지시 입력...", key=f"chat_{proj_name}")

# =========================================================
# ⚖️ 4. 품질관리 (QC)
# =========================================================
with tab_qc:
    st.info("QC팀 대기 중")