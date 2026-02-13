import streamlit as st
import sys
import time
import pandas as pd
from pathlib import Path

# =========================================================
# 🏗️ [Path Safety] 경로 고속도로 (Path Fix)
# =========================================================
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent

# 시스템 경로 확보 (백엔드 모듈 로딩용)
if str(CURRENT_DIR) not in sys.path: sys.path.append(str(CURRENT_DIR))
if str(ROOT_DIR) not in sys.path: sys.path.append(str(ROOT_DIR))

# 1. 시스템 유틸리티 로드
try:
    import system_utils as utils
except ImportError:
    pass

# 2. 🔥 [Core Engine] 전략기획실 두뇌 연결 (strategy_judge)
try:
    import strategy_judge as engine
except ImportError:
    engine = None

# 3. 시각화 도구 로드
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# =========================================================
# 📊 [Visualizer] 데이터 시각화 함수
# =========================================================
def draw_radar_chart(plan_data):
    """기획안의 5각 능력치(육각형) 그래프 생성"""
    if not HAS_PLOTLY: return None
    
    # 데이터가 없으면 기본값으로 방어
    stats = plan_data.get('stats', {
        "대중성": 50, "독창성": 50, "캐릭터": 50, "개연성": 50, "확장성": 50
    })
    
    df = pd.DataFrame(dict(
        r=list(stats.values()),
        theta=list(stats.keys())
    ))
    
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B') # 강렬한 레드
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=300
    )
    return fig

# =========================================================
# 🚀 [Main UI] 렌더링 로직 (Master-Detail Pattern)
# =========================================================
def render(planning_dir):
    st.markdown("## 🗂️ 기획 창고 (Warehouse)")
    st.caption("📦 보유한 IP를 관리하고, **[제작소 투입]** 및 **[리메이크(Develop)]**를 수행합니다.")

    # 1. [Data Fetching] 프로젝트 폴더 스캔
    try:
        if not planning_dir.exists():
            st.error("기획 폴더 경로가 존재하지 않습니다.")
            return
            
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True) # 최신순 정렬
    except Exception as e:
        st.error(f"폴더 스캔 오류: {e}")
        projs = []

    if not projs:
        st.info("📭 보관된 기획안이 없습니다. [전략기획실]에서 신규 IP를 발굴하세요.")
        return

    # -----------------------------------------------------
    # 2. [Master View] 프로젝트 선택기
    # -----------------------------------------------------
    proj_map = {p.name: p for p in projs}
    proj_names = list(proj_map.keys())
    
    selected_proj_name = st.selectbox(
        "📂 **열람할 프로젝트를 선택하세요:**", 
        proj_names, 
        index=0
    )
    
    selected_folder = proj_map[selected_proj_name]
    data = utils.load_project_data(selected_folder)

    if not data:
        st.warning("⚠️ 데이터 로드 실패 (파일 손상 가능성)")
        return

    # -----------------------------------------------------
    # 3. [Detail View] 상세 대시보드
    # -----------------------------------------------------
    st.divider()
    
    # [Header] 제목 및 상태
    c_head_1, c_head_2 = st.columns([3, 1])
    with c_head_1:
        title_text = data.get('title', '무제')
        ver_text = data.get('version', '1.0')
        st.markdown(f"### 📄 {title_text} <span style='color:gray; font-size:0.6em'>v{ver_text}</span>", unsafe_allow_html=True)
        st.caption(f"**Last Updated:** {time.ctime(selected_folder.stat().st_mtime)}")
    with c_head_2:
        st.info(f"**장르:** {data.get('genre', '미정')}")

    # [Dashboard Grid]
    col_left, col_right = st.columns([1.2, 2])

    # --- [Left Column] 분석 및 컨트롤 ---
    with col_left:
        # 1. 레이더 차트
        with st.container(border=True):
            st.markdown("##### 📊 IP 파워 분석")
            if HAS_PLOTLY:
                fig = draw_radar_chart(data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.progress(data.get('stats', {}).get('대중성', 50) / 100)
                st.caption("그래프 엔진 없음")
            
            # SWOT 요약
            swot = data.get('swot_analysis', {})
            if swot:
                st.success(f"**S:** {swot.get('strength', '-')[:30]}...")
                st.error(f"**W:** {swot.get('weakness', '-')[:30]}...")

        # 2. 액션 센터 (핵심 기능)
        st.markdown("### ⚡ Action Center")
        
        # [A] 제작소 투입
        with st.expander("🏭 **제작 스튜디오 투입**", expanded=True):
            slot = st.selectbox("스튜디오 슬롯", [f"Studio {i}" for i in range(1, 11)], key="slot_selector")
            
            if st.button("🚀 **제작 착수 (Start)**", type="primary", use_container_width=True):
                if 'active_projects' not in st.session_state: 
                    st.session_state.active_projects = []
                
                if selected_folder.name not in st.session_state.active_projects:
                    st.session_state.active_projects.append(selected_folder.name)
                    st.toast(f"✅ '{title_text}' 제작 승인! ({slot})", icon="🎬")
                    time.sleep(1)
                else:
                    st.warning("이미 제작 중인 프로젝트입니다.")

        # [B] 리메이크 (백엔드 호출)
        with st.expander("🛠️ **기획 디벨롭 (Remake)**"):
            st.markdown("**수석 기획자(AI)에게 수정을 지시합니다.**")
            req_text = st.text_area("수정 지시사항", placeholder="예: 주인공을 더 악랄하게 바꾸고, 3화 위기를 강화해.")
            
            if st.button("✨ **분석 및 수정 실행**", use_container_width=True):
                if not engine:
                    st.error("❌ 기획 엔진(strategy_judge)이 로드되지 않았습니다.")
                else:
                    with st.status("🧠 **전략기획실에서 데이터를 분석 중입니다...**", expanded=True) as status:
                        st.write("1️⃣ 원본 분석 및 지시사항 해석...")
                        # 백엔드 호출
                        new_p, logs = engine.remake_planning(data, req_text)
                        
                        st.write("2️⃣ 기획 수정 및 레드팀 검증...")
                        
                        # 분석 결과 보여주기
                        if new_p.get('remake_analysis'):
                            ra = new_p['remake_analysis']
                            st.info(f"**[분석 결과]**\n- 👍 장점: {ra.get('pros')}\n- ⚖️ 판단: {ra.get('verdict')}")
                        
                        # 새 버전 저장
                        utils.create_new_version(selected_folder, new_p)
                        status.update(label="✅ **vUp 완료! (새 버전 저장됨)**", state="complete")
                        
                        time.sleep(2)
                        st.rerun()

        # [C] 폐기
        if st.button("🗑️ **프로젝트 영구 삭제**", use_container_width=True):
            utils.delete_project(selected_folder)
            st.toast("프로젝트가 삭제되었습니다.")
            time.sleep(1)
            st.rerun()

    # --- [Right Column] 문서 내용 ---
    with col_right:
        tab1, tab2, tab3 = st.tabs(["📜 **시놉시스 & 플롯**", "👥 **캐릭터 & 세계관**", "💡 **세일즈 포인트**"])
        
        with tab1:
            st.info(f"**Logline:** {data.get('logline')}")
            st.markdown("#### 🎬 시놉시스")
            st.write(data.get('synopsis'))
            
            st.divider()
            st.markdown("#### 📅 회차별 플롯")
            for p in data.get('episode_plots', []):
                with st.expander(f"**[{p.get('ep')}화]** {p.get('title')}"):
                    st.write(p.get('summary'))

        with tab2:
            st.markdown("#### 👥 등장인물")
            for c in data.get('characters', []):
                role = c.get('role', 'Extra')
                emoji = "👑" if "Main" in role or "주인공" in role else "⚔️" if "Antagonist" in role else "👤"
                with st.container(border=True):
                    st.markdown(f"**{emoji} {c.get('name')}** _({role})_")
                    st.caption(f"MBTI: {c.get('mbti', '?')} | {c.get('desc')}")
            
            st.markdown("#### 🌍 세계관")
            st.write(data.get('world_view'))

        with tab3:
            st.markdown("#### 💰 세일즈 포인트")
            for sp in data.get('sales_points', []):
                st.markdown(f"✅ {sp}")
            
            st.markdown("#### 🚨 레드팀 리포트")
            rt = data.get('red_team_critique', {})
            if rt:
                st.warning(f"**지적:** {rt.get('warning', '-')}")
                st.success(f"**해결:** {rt.get('solution', '-')}")