import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏗️ [Setup] 경로 안전장치 (Path Safety)
# =========================================================
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

# 시스템 경로에 강제 주입 (ModuleNotFoundError 방지)
if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 엔진 로드
try:
    import strategy_judge as engine
except ImportError:
    engine = None

def render():
    st.markdown("## 🧠 전략 기획실 (Strategic Planning Room)")
    st.caption("🚀 아이디어 투입 ➔ 3라운드 기획 토론 ➔ 최종 기획안 도출")

    # 1. 엔진 점검
    if not engine:
        st.error("❌ **시스템 오류:** `strategy_judge.py`를 로드할 수 없습니다.")
        return

    # 2. [Input] 아이디어 입력 패널
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            mode = st.radio("🛠️ **기획 모드**", ["1. 신규 기획", "2. 소재 개발", "3. 심폐소생"], index=0)
            mode_map = {"1. 신규 기획": 1, "2. 소재 개발": 2, "3. 심폐소생": 3}
        
        with c2:
            user_input = st.text_area(
                "💡 **아이디어 / 로그라인 / 키워드 입력**", 
                height=120, 
                placeholder="예: 재벌가 망나니로 회귀했는데 알고 보니 시한부였다. 1년 안에 그룹을 장악해야 산다."
            )
            
            # 실행 버튼
            if st.button("🔥 **기획 엔진 가동 (Start Engine)**", type="primary", use_container_width=True):
                if not user_input.strip():
                    st.warning("⚠️ 아이디어를 입력해주세요.")
                else:
                    # 3. [Process] 기획 엔진 실행
                    with st.status("🤖 **AI 기획팀이 회의를 시작했습니다...**", expanded=True) as status:
                        st.write("🔍 **[1단계]** 트렌드 분석 및 세계관 설정 중...")
                        time.sleep(1)
                        st.write("🥊 **[2단계]** 레드팀(Red Team) 비평 및 논리 검증 진행...")
                        
                        # 실제 엔진 호출
                        final_plan, logs = engine.process_planning(mode_map[mode], user_input)
                        
                        st.text_area("📝 **회의록 (Debug Log)**", logs, height=150)
                        
                        status.update(label="✅ **기획안 도출 완료!**", state="complete", expanded=False)
                        
                        # 결과 세션 저장
                        st.session_state.current_plan = final_plan
                        st.rerun()

    # 4. [Output] 최종 기획안 리포트
    if st.session_state.get('current_plan'):
        plan = st.session_state.current_plan
        
        # 데이터 손상 체크
        if plan.get('is_corrupted'):
            st.error(f"❌ 기획 생성 실패: {plan.get('logline')}")
            return

        st.divider()
        
        # --- [Report Header] ---
        st.markdown(f"# 📑 {plan.get('title', '무제')}")
        st.caption(f"**장르:** {plan.get('genre', '-')} | **키워드:** {', '.join(plan.get('keywords', []))}")

        # [Red Team Score]
        critique = plan.get('red_team_critique', {})
        score = critique.get('score', 0)
        score_color = "green" if score >= 85 else "orange" if score >= 70 else "red"
        st.markdown(f"### 📊 기획 점수: :{score_color}[**{score}점**]")
        
        if critique.get('warning'):
            st.warning(f"⚠️ **Red Team 지적:** {critique.get('warning')}")

        # --- [Tab View] 상세 내용 ---
        t1, t2, t3, t4 = st.tabs(["📜 **핵심 요약**", "👥 **캐릭터**", "🗺️ **플롯**", "💰 **전략**"])
        
        # Tab 1: 핵심 요약
        with t1:
            with st.container(border=True):
                st.markdown("#### 🎯 로그라인 (Logline)")
                st.info(plan.get('logline', '-'))
                
                st.markdown("#### 💡 기획 의도 (Planning Intent)")
                st.write(plan.get('planning_intent', '-'))
                
                st.markdown("#### 🌍 세계관 (World View)")
                st.write(plan.get('world_view', '-'))

        # Tab 2: 캐릭터
        with t2:
            chars = plan.get('characters', [])
            if chars:
                # 주인공 강조
                main = chars[0]
                with st.container(border=True):
                    c_icon, c_info = st.columns([1, 6])
                    with c_icon: st.markdown("# 👑")
                    with c_info:
                        st.markdown(f"**{main.get('name')}** (주인공)")
                        st.caption(f"MBTI: {main.get('mbti', '-')} | 역할: {main.get('role')}")
                        st.write(main.get('desc'))
                
                # 조연 리스트
                col_sub1, col_sub2 = st.columns(2)
                for i, char in enumerate(chars[1:]):
                    with (col_sub1 if i % 2 == 0 else col_sub2).container(border=True):
                        st.markdown(f"**{char.get('name')}**")
                        st.caption(char.get('role'))
                        st.write(char.get('desc'))

        # Tab 3: 플롯
        with t3:
            st.markdown("#### 🎬 전체 줄거리")
            st.write(plan.get('synopsis', '-'))
            
            st.markdown("#### 🎞️ 초반 회차별 플롯")
            for p in plan.get('episode_plots', []):
                with st.expander(f"**[{p.get('ep')}화] {p.get('title')}**"):
                    st.write(p.get('summary'))

        # Tab 4: 전략 (SWOT & Sales)
        with t4:
            swot = plan.get('swot_analysis', {})
            if swot:
                c_s, c_w = st.columns(2)
                c_s.success(f"**Strength:** {swot.get('strength')}")
                c_w.error(f"**Weakness:** {swot.get('weakness')}")
                
            st.markdown("#### 💰 세일즈 포인트")
            for sp in plan.get('sales_points', []):
                st.markdown(f"✅ {sp}")

        # --- [Footer Action] ---
        st.divider()
        col_save, col_discard = st.columns([1, 1])
        
        with col_save:
            if st.button("💾 **승인 및 창고 입고 (Save)**", type="primary", use_container_width=True):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("✅ 기획안이 창고에 안전하게 입고되었습니다!", icon="📦")
                    time.sleep(1.5)
                    st.session_state.current_plan = None
                    st.rerun()
                else:
                    st.error(f"저장 실패: {msg}")
        
        with col_discard:
            if st.button("🗑️ **폐기 (Discard)**", use_container_width=True):
                st.session_state.current_plan = None
                st.rerun()