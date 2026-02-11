import streamlit as st
import time

# =========================================================
# 🏭 AI Novel Factory (Frontend Simulation)
# DB 연결 없이 화면 구성을 확인하기 위한 '껍데기' 코드입니다.
# =========================================================

st.set_page_config(page_title="AI 소설 공장 (Demo)", layout="wide")

# 가짜 DB 역할을 할 세션 상태 초기화
if "jobs" not in st.session_state:
    st.session_state.jobs = []

st.title("🏭 AI 소설 공장 컨트롤 타워 (Simulation Mode)")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["💡 기획실 (Planning)", "✍️ 제작소 (Production)", "✅ 품질관리 (QC)"])

# --- [사장님이 보고 싶어 하신 제작소 탭] ---
with tab2:
    st.header("✍️ 멀티 제작 스튜디오 (Production Studio)")
    
    # 1:2 비율로 화면 분할
    col1, col2 = st.columns([1, 2])
    
    # [왼쪽] 작업 지시 패널
    with col1:
        st.markdown("### 📡 작업 지시 (Commander)")
        st.info("집필할 작품과 화수를 선택하고 투입 버튼을 누르세요.")
        
        project_list = ["아포칼립스 물류팀장", "망국 횡령 징수관", "재벌집 막내 AI"] 
        target_project = st.selectbox("작품 선택", project_list)
        target_chapter = st.number_input("집필할 화수", min_value=1, value=1)
        
        # 버튼을 누르면 가짜 작업이 추가됨
        if st.button("🔥 1팀 투입 (집필 시작)", type="primary"):
            # 가짜 데이터 생성
            new_job = {
                'team_id': 'Team 1',
                'project_title': target_project,
                'chapter_num': target_chapter,
                'status': 'processing',
                'progress': 0
            }
            st.session_state.jobs.append(new_job)
            st.success(f"✅ 명령 하달 완료: '{target_project}' {target_chapter}화")
            time.sleep(0.5) # 약간의 딜레이 연출
            st.rerun() # 화면 새로고침

    # [오른쪽] 공장 가동 현황판
    with col2:
        st.markdown("### 🏭 공장 가동 현황 (Real-time Monitor)")
        
        # 작업 중인 놈들만 필터링해서 보여줌
        active_jobs = [j for j in st.session_state.jobs if j['status'] == 'processing']
        
        if active_jobs:
            for i, job in enumerate(active_jobs):
                # 시각적 연출 (카드 형태)
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.warning(f"⚙️ **[{job['team_id']}] {job['project_title']}** - 제 {job['chapter_num']}화 집필 중...")
                    with c2:
                        st.caption("Status: Running")
                    
                    # 가짜 진행률 (새로고침 할 때마다 조금씩 참)
                    job['progress'] += 10
                    if job['progress'] > 100: job['progress'] = 100
                    st.progress(job['progress'])
                    
                    st.text(f"현재 공정: 텍스트 생성 중... ({job['progress']}%)")
                    
                    # (테스트용) 작업 강제 종료 버튼
                    if st.button(f"작업 완료 처리 (Test) #{i}"):
                        job['status'] = 'completed'
                        st.rerun()
        else:
            # 작업 없을 때 보여줄 화면
            st.info("💤 현재 가동 중인 라인이 없습니다. (대기 상태)")
            st.markdown("""
            > **[System Status]**
            > * **Team 1:** Idle (대기)
            > * **Team 2:** Idle (대기)
            > * **Server:** Online
            """)

# --- 다른 탭 (구색 맞추기) ---
with tab1:
    st.info("기획실 화면입니다. (현재 제작소 탭 시연 중)")

with tab3:
    st.info("QC 화면입니다. 완료된 원고가 여기에 표시됩니다.")
    
    # 완료된 작업 보여주기
    completed_jobs = [j for j in st.session_state.jobs if j['status'] == 'completed']
    if completed_jobs:
        st.success(f"총 {len(completed_jobs)}건의 원고가 검수를 기다리고 있습니다.")
        for job in completed_jobs:
            with st.expander(f"📄 [완료] {job['project_title']} {job['chapter_num']}화"):
                st.write("여기에 AI가 쓴 본문 내용이 들어갑니다... (블라블라)")
                st.button(f"승인 및 출고 #{job['chapter_num']}")