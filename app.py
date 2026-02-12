import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V5 (Report UI & Action System)
# =========================================================

# 1. 경로 설정 (03번 방 엔진 연결)
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
sys.path.append(str(planning_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 엔진 로드 (안전장치 포함)
try:
    import strategy_judge as engine
    engine.init_engine()
    ENGINE_STATUS = "🟢 엔진 정상"
    MODEL_INFO = getattr(engine, 'MODEL_NAME', 'Unknown')
except ImportError:
    ENGINE_STATUS = "🔴 엔진 연결 실패 (경로 확인 필요)"
    MODEL_INFO = "Unknown"

# 3. 헤더
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

# 4. 세션 상태 초기화
if "plan_history" not in st.session_state:
    st.session_state.plan_history = [] 
if "current_plan" not in st.session_state:
    st.session_state.current_plan = None 

# 5. 탭 구성
tab_plan, tab_write, tab_qc = st.tabs(["💡 1. 기획실", "✍️ 2. 제작소", "⚖️ 3. 품질관리"])

# =========================================================
# 💡 1. 기획실 (Strategy Room)
# =========================================================
with tab_plan:
    st.subheader("🧠 전략 기획실 (Strategy Room)")
    
    c1, c2 = st.columns([1, 1.5])
    
    # --- [왼쪽] 입력 패널 ---
    with c1:
        st.info("🛠️ 작전 지시")
        mode_idx = st.radio("모드 선택", ["1. 오리지널 (자동)", "2. 유저 기획 (발전)", "3. 심폐소생 (수정)"], index=0)
        user_input = st.text_area("키워드 / 아이디어 / 문제점 입력", height=150, placeholder="예: 회귀물인데 주인공이 재벌집 막내아들인 설정으로 기획해줘.")
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "🔴" in ENGINE_STATUS:
                st.error("엔진이 연결되지 않았습니다.")
            else:
                with st.spinner("PD가 머리를 굴리고 있습니다... (약 10~20초 소요)"):
                    mode_num = int(mode_idx[0])
                    # 엔진 호출
                    res, logs = engine.process_planning(mode_num, user_input)
                    st.session_state.current_plan = res
                    st.session_state.logs = logs
                    st.rerun()

    # --- [오른쪽] 보고서 패널 ---
    with c2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            
            # 1. 헤더 (제목/장르/키워드)
            st.markdown(f"# 📑 {plan.get('title', '제목 미정')}")
            
            # 키워드 리스트 처리
            keywords = plan.get('keywords', [])
            kw_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
            
            st.markdown(f"**장르:** {plan.get('genre')} | **키워드:** {kw_str}")
            
            # 2. 로그라인 (강조)
            st.info(f"💡 **로그라인:** {plan.get('logline')}")
            
            # 3. 상세 내용 (아코디언 스타일)
            with st.expander("📌 3. 기획 의도", expanded=True):
                st.write(plan.get('planning_intent', '내용 없음'))
                
            with st.expander("👥 4. 등장인물", expanded=True):
                chars = plan.get('characters', [])
                if chars:
                    for char in chars:
                        if isinstance(char, dict):
                            st.markdown(f"**{char.get('name', '?')}** ({char.get('role', '역할')}) : {char.get('desc', '')}")
                        else:
                            st.write(f"- {char}")
                else:
                    st.write("등장인물 데이터 없음")
            
            with st.expander("📜 5. 줄거리 (시놉시스)", expanded=True):
                st.write(plan.get('synopsis', '내용 없음'))
                
            with st.expander("🔥 6. 차별화 포인트", expanded=True):
                points = plan.get('selling_points', [])
                for p in points:
                    st.write(f"- {p}")
            
            # 4. PD 평가
            st.caption(f"🏁 PD 코멘트: {plan.get('pd_comment', '코멘트 없음')}")
            st.markdown("---")
            
            # 5. 결재 시스템 (버튼)
            st.write("### 👑 사장님 결재")
            
            col_approve, col_reject, col_trash = st.columns(3)
            
            # [승인]
            if col_approve.button("✅ 승인 (제작 착수)"):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("🎉 제작소로 이관되었습니다!", icon="🚀")
                    st.success(msg)
                    time.sleep(1)
                    # 여기서 탭 이동 기능을 넣을 수도 있음
                else:
                    st.error(msg)
            
            # [반려]
            with col_reject.popover("⚠️ 반려 (수정 지시)"):
                feedback = st.text_area("수정 지시사항 (구체적으로)")
                if st.button("수정 요청 전송"):
                    with st.spinner("지시사항 반영하여 재기획 중..."):
                        mode_num = int(mode_idx[0])
                        # 재호출 (피드백 포함)
                        res, logs = engine.process_planning(mode_num, user_input, feedback_history=feedback)
                        st.session_state.current_plan = res
                        st.rerun()

            # [폐기]
            if col_trash.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()

        else:
            st.info("👈 왼쪽 패널에서 아이디어를 입력하고 [엔진 가동]을 눌러주세요.")
            st.markdown("""
            **[사용 가이드]**
            1. **오리지널 모드**: 키워드 하나만 줘도 AI가 알아서 만듭니다.
            2. **유저 기획**: 사장님의 아이디어를 구체화합니다.
            3. **심폐소생**: 설정 구멍이 있는 글을 고쳐줍니다.
            """)

# =========================================================
# ✍️ 2. 제작소 (V3 유지 - 구글 닥스 연동 예정)
# =========================================================
with tab_write:
    st.info("기획실에서 [승인] 버튼을 누르면, 이곳에 '제작 지시서'가 도착합니다.")
    # (추후 구글 닥스 생성 로직 연결)

# =========================================================
# ⚖️ 3. 품질관리 (V3 유지)
# =========================================================
with tab_qc:
    st.info("QC팀 대기 중")