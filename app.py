import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V5 (Path Fixed & Engine Connected)
# =========================================================

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 🚨 [경로 문제 해결] 03번 폴더를 강제로 인식시킴
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
sys.path.append(str(planning_dir))

# 엔진 호출 시도
ENGINE_STATUS = "연결 대기중..."
try:
    import strategy_judge as engine
    success, msg = engine.init_engine()
    if success:
        ENGINE_STATUS = "🟢 엔진 정상 (Connected)"
    else:
        ENGINE_STATUS = f"🔴 엔진 에러: {msg}"
except ImportError:
    ENGINE_STATUS = "❌ 경로 에러 (03_전략기획실_Planning 폴더를 못 찾음)"

# --- [UI 시작] ---
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS}")

tab_plan, tab_write, tab_qc = st.tabs(["💡 1. 기획실", "✍️ 2. 제작소", "⚖️ 3. 품질관리"])

# ---------------------------------------------------------
# 💡 1. 기획실 (실제 엔진 연동)
# ---------------------------------------------------------
with tab_plan:
    st.subheader("🧠 전략 기획실 (Strategy Room)")
    
    col_input, col_result = st.columns([1, 1.5])
    
    with col_input:
        st.info("사장님의 지시를 입력하십시오.")
        
        # 3가지 모드 선택 (사장님 지시 반영)
        mode_select = st.radio("작전 모드", 
            ["1. 오리지널 (완전 자동)", "2. 유저 기획 (아이디어 발전)", "3. 심폐소생 (망한 글 살리기)"])
        
        user_input = st.text_area("키워드 / 아이디어 / 문제점 입력", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "❌" in ENGINE_STATUS:
                st.error("엔진이 연결되지 않았습니다. 파일 위치를 확인하세요.")
            else:
                mode_map = {"1": 1, "2": 2, "3": 3}
                mode_num = mode_map[mode_select[0]] # 1, 2, 3 숫자 추출
                
                with st.spinner("PD가 분석 중입니다..."):
                    # [백엔드 호출]
                    result, logs = engine.process_planning(mode_num, user_input)
                    
                    # 결과를 세션에 저장 (화면 유지용)
                    st.session_state['last_plan'] = result
                    st.session_state['last_logs'] = logs
                    st.success("완료!")

    with col_result:
        st.markdown("##### 📄 기획 결과 리포트")
        if 'last_plan' in st.session_state:
            data = st.session_state['last_plan']
            
            st.markdown(f"### 🏷️ 제목: {data.get('title', '무제')}")
            st.write(f"**장르:** {data.get('genre', '미정')}")
            st.info(f"**로그라인:** {data.get('logline', '-')}")
            
            st.write("**🔥 셀링 포인트:**")
            for point in data.get('selling_points', []):
                st.write(f"- {point}")
                
            with st.expander("🔍 처리 로그 확인"):
                st.text(st.session_state['last_logs'])
                
            st.button("💾 이 기획으로 제작소(2팀) 전달")

# ---------------------------------------------------------
# ✍️ 2. 제작소 & 3. 품질관리 (V3 유지)
# ---------------------------------------------------------
with tab_write:
    st.info("기획실에서 [전달] 버튼을 누르면 여기서 구글 닥스 집필이 시작됩니다.")

with tab_qc:
    st.info("QC팀 대기 중.")