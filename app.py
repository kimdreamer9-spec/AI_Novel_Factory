import streamlit as st
import sys
import time
import json
import os
import shutil
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V8 (Warehouse Remake System)
# =========================================================

# 1. 경로 설정
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

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
    """통합 데이터 로드 (신형/구형 호환)"""
    # 1. 신형
    json_path = folder_path / "Approved_Plan.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    
    # 2. 구형
    drafts = list(folder_path.glob("기획안_Draft*.json"))
    if drafts:
        try:
            drafts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            with open(drafts[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                # 구형 데이터 매핑
                if '1_작품_기본_정보' in data:
                    flat_data = {}
                    info = data.get('1_작품_기본_정보', {})
                    flat_data['title'] = info.get('제목', folder_path.name)
                    flat_data['genre'] = info.get('장르', '미상')
                    flat_data['logline'] = data.get('3_작품_소개_로그라인', '로그라인 없음')
                    flat_data['synopsis'] = "구형 데이터입니다. 리메이크를 통해 정보를 갱신하세요."
                    flat_data['characters'] = []
                    flat_data['selling_points'] = []
                    return flat_data
                return data
        except: pass
    
    return {"title": folder_path.name, "logline": "데이터 호환 불가", "genre": "미상"}

def update_project_file(folder_path, new_plan_data):
    """리메이크된 기획안 덮어쓰기"""
    try:
        # 기존 파일 백업 (혹시 모르니까)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = folder_path / f"Backup_{timestamp}.json"
        if (folder_path / "Approved_Plan.json").exists():
            shutil.copy(folder_path / "Approved_Plan.json", backup_path)
            
        # 새 파일 저장
        (folder_path / "Approved_Plan.json").write_text(json.dumps(new_plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True, "업데이트 성공"
    except Exception as e:
        return False, str(e)

def move_to_production(project_name):
    if 'active_projects' not in st.session_state:
        st.session_state.active_projects = []
    if project_name not in st.session_state.active_projects:
        st.session_state.active_projects.append(project_name)
    return True

def delete_project(folder_path):
    try:
        shutil.rmtree(folder_path)
        return True
    except: return False

# 4. 헤더
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 탭 구성
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
        user_input = st.text_area("키워드 / 아이디어", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "🔴" in ENGINE_STATUS:
                st.error("엔진 에러")
            else:
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
            
            # 리스크 리포트
            risk = plan.get('risk_report', {})
            if risk.get('detected'):
                st.error(f"🚨 경고: {risk.get('red_team_warning')}")
                st.info(f"💡 대안: {risk.get('alternative_suggestion')}")

            with st.expander("상세 내용 보기", expanded=True):
                st.write(f"**기획의도:** {plan.get('planning_intent')}")
                st.write(f"**시놉시스:** {plan.get('synopsis')}")
            
            col_save, col_fix = st.columns(2)
            if col_save.button("💾 승인 및 입고"):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("창고 입고 완료!", icon="📦")
                    st.session_state.current_plan = None
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
            
            if col_fix.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()

# =========================================================
# 🗂️ 2. 기획 창고 (Warehouse) - [핵심 기능 추가됨]
# =========================================================
with tab_warehouse:
    st.subheader("📦 기획안 보관소 & 숙성실")
    st.caption("기획안을 투입하거나, '리메이크'를 통해 내용을 발전시킬 수 있습니다.")

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
            
            with st.expander(f"📁 {data.get('title')} ({proj_dir.name})"):
                c_info, c_action = st.columns([2.5, 1])
                
                with c_info:
                    st.markdown(f"**장르:** {data.get('genre')}")
                    st.info(f"**로그라인:** {data.get('logline')}")
                    st.caption(f"시스템 경로: {proj_dir.name}")
                    if st.checkbox("상세 내용 보기", key=f"view_{proj_dir.name}"):
                        st.write(data.get('synopsis'))
                        st.json(data.get('characters'))
                
                with c_action:
                    # 1. 제작 투입
                    if proj_dir.name in st.session_state.active_projects:
                        st.success("✅ 제작 가동 중")
                    else:
                        if st.button("🚀 제작 투입", key=f"deploy_{proj_dir.name}"):
                            move_to_production(proj_dir.name)
                            st.toast("제작 라인으로 이동!", icon="🔥")
                            st.rerun()
                    
                    # 2. 🔥 리메이크 (디벨롭) - 창고 내 즉시 반영
                    with st.popover("🛠️ 리메이크 (수정)"):
                        st.write("🤖 AI에게 수정 지시를 내립니다.")
                        remake_txt = st.text_area("예: 주인공 이름을 '강철'로 바꾸고, 결말을 해피엔딩으로 수정해.", key=f"re_txt_{proj_dir.name}")
                        
                        if st.button("수정 실행", key=f"do_remake_{proj_dir.name}", type="primary"):
                            with st.spinner("기획안을 뜯어고치는 중..."):
                                # 문맥 주입
                                context = f"기존 제목: {data.get('title')}\n기존 시놉: {data.get('synopsis')}"
                                # 엔진 호출
                                new_plan, _ = engine.process_planning(2, context, feedback_history=remake_txt)
                                
                                # 파일 덮어쓰기
                                succ, msg = update_project_file(proj_dir, new_plan)
                                
                                if succ:
                                    st.success("수정 완료! 화면을 갱신합니다.")
                                    time.sleep(1)
                                    st.rerun() # [핵심] 여기서 새로고침해서 바로 바뀐 내용을 보여줌
                                else:
                                    st.error(f"오류: {msg}")

                    # 3. 삭제
                    if st.button("🗑️ 영구 삭제", key=f"del_{proj_dir.name}"):
                        delete_project(proj_dir)
                        st.rerun()

# =========================================================
# ✍️ 3. 제작소 (Production)
# =========================================================
with tab_production:
    st.subheader("🏭 실시간 제작 현황")
    
    active_list = st.session_state.active_projects
    
    if not active_list:
        st.info("현재 가동 중인 라인이 없습니다. [기획 창고]에서 작품을 투입해주세요.")
    else:
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
                    if st.button("⏹️ 제작 중단", key=f"stop_{proj_name}"):
                        st.session_state.active_projects.remove(proj_name)
                        st.rerun()

                with col_chat:
                    st.write("💬 **집필 AI 지시 (Command Center)**")
                    st.chat_message("assistant").write(f"'{data.get('title')}' 집필 준비 완료. 1화 작성을 시작할까요?")
                    st.chat_input(f"지시 입력...", key=f"chat_{proj_name}")

# =========================================================
# ⚖️ 4. 품질관리 (QC)
# =========================================================
with tab_qc:
    st.info("QC팀 대기 중")