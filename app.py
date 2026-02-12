import streamlit as st
import sys
import time
import json
import os
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V6 (Planning -> Production Connected)
# =========================================================

# 1. 경로 설정 (03번 방 엔진 연결)
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
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

# 3. 헤더
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO} | Storage: Local (Codespace)")

# 4. 세션 상태
if "current_plan" not in st.session_state: st.session_state.current_plan = None 

tab_plan, tab_write, tab_qc = st.tabs(["💡 1. 기획실", "✍️ 2. 제작소", "⚖️ 3. 품질관리"])

# =========================================================
# 💡 1. 기획실 (Strategy Room) - 기존 유지
# =========================================================
with tab_plan:
    st.subheader("🧠 전략 기획실")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode_idx = st.radio("모드", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        user_input = st.text_area("키워드 입력", height=150)
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
            with st.expander("상세 보기", expanded=True):
                st.write(plan.get('synopsis'))
            
            st.write("### 👑 사장님 결재")
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("✅ 승인 (제작 착수)"):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("제작소로 이관 완료!", icon="🚀")
                    st.success(msg)
                    time.sleep(1)
                    st.rerun() # 화면 갱신해서 제작소에 반영
                else: st.error(msg)
            # (반려/폐기 버튼 생략 - 위 코드와 동일)

# =========================================================
# ✍️ 2. 제작소 (Production Studio) - 🔥 여기가 핵심 수정됨
# =========================================================
with tab_write:
    st.subheader("✍️ 메인 집필실 (Writer's Room)")
    
    # 1. 03번 폴더 스캔하여 프로젝트 목록 가져오기
    # (폴더이면서 __pycache__가 아닌 것들)
    try:
        projects = [f.name for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith("__") and not f.name.startswith(".")]
        projects.sort(reverse=True) # 최신순 정렬
    except Exception as e:
        projects = []
        st.error(f"폴더 스캔 실패: {e}")

    # 2. 프로젝트 선택 UI
    col_list, col_work = st.columns([1, 2])
    
    with col_list:
        st.markdown("### 📂 프로젝트 보관함")
        if not projects:
            st.warning("진행 중인 프로젝트가 없습니다. 기획실에서 승인해주세요.")
        else:
            selected_project_name = st.radio("작업할 소설 선택", projects)
            
            # 선택된 폴더 경로
            selected_path = planning_dir / selected_project_name
            
            # 파일 로드 시도
            try:
                json_path = selected_path / "Approved_Plan.json"
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        project_data = json.load(f)
                    st.success(f"✅ '{selected_project_name}' 로드 완료")
                else:
                    project_data = None
                    st.warning("⚠️ 승인된 기획안 파일(Approved_Plan.json)이 없습니다.")
            except Exception as e:
                st.error(f"로드 에러: {e}")
                project_data = None

    # 3. 작업 공간 UI
    with col_work:
        if project_data:
            st.markdown(f"## 📝 집필 중: {project_data.get('title')}")
            
            with st.expander("📚 설정 자료 (기획안 요약)", expanded=False):
                st.write(f"**장르:** {project_data.get('genre')}")
                st.write(f"**로그라인:** {project_data.get('logline')}")
                st.write("**등장인물:**")
                st.json(project_data.get('characters'))

            # (여기서 구글 닥스 링크가 생성될 예정)
            st.info("👇 [집필 AI]에게 명령을 내려주세요.")
            
            # 채팅 인터페이스 (집필용)
            if "messages" not in st.session_state: st.session_state.messages = []

            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

            if prompt := st.chat_input("예: 1화 도입부 써줘 (구글 닥스 연동 예정)"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.chat_message("user").write(prompt)
                
                # (가짜 응답 - 추후 실제 연동)
                response = f"알겠습니다. '{project_data.get('title')}'의 설정을 바탕으로 집필을 시작합니다... (시스템 준비 중)"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
        else:
            st.info("👈 왼쪽에서 프로젝트를 선택하면 작업 공간이 열립니다.")

# =========================================================
# ⚖️ 3. 품질관리 (QC)
# =========================================================
with tab_qc:
    st.info("QC팀 대기 중")