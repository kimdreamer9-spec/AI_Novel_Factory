import streamlit as st
import sys
import pandas as pd
from pathlib import Path

# =========================================================
# 🏗️ [Setup] 환경 및 경로 설정
# =========================================================
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 🔥 [Engine] 창고는 '개발/수정' 담당인 manager_development와 연결
try: import manager_development as engine
except: engine = None
try: import system_utils as utils
except: pass

# 시각화 도구
try:
    import plotly.express as px
    HAS_PLOTLY = True
except: HAS_PLOTLY = False

# =========================================================
# 📊 [Visualizer] 차트 및 시각화 함수
# =========================================================
def draw_radar_chart(plan_data):
    """오각형 레이더 차트 (작품 밸런스 분석)"""
    if not HAS_PLOTLY: return None
    # 데이터가 없으면 기본값으로 채움
    stats = plan_data.get('stats', {"대중성":70, "독창성":60, "캐릭터":80, "개연성":70, "확장성":60})
    
    df = pd.DataFrame(dict(r=list(stats.values()), theta=list(stats.keys())))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B')
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=250,
        showlegend=False
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
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True) # 최신순 정렬
    except: projs = []

    if not projs:
        st.info("📭 보관된 기획안이 없습니다. [전략기획실]에서 신규 IP를 발굴하세요.")
        return

    # -----------------------------------------------------
    # 2. [Master View] 프로젝트 선택기 (가로형 리스트)
    # -----------------------------------------------------
    # 프로젝트 이름만 추출하여 선택 박스 생성
    proj_map = {p.name: p for p in projs}
    proj_names = list(proj_map.keys())
    
    selected_proj_name = st.selectbox(
        "📂 **열람할 프로젝트를 선택하세요:**", 
        proj_names, 
        index=0,
        help="목록에서 프로젝트를 선택하면 상세 대시보드가 열립니다."
    )
    
    selected_folder = proj_map[selected_proj_name]
    data = utils.load_project_data(selected_folder)

    if not data:
        st.error("데이터 로드 실패")
        return

    # -----------------------------------------------------
    # 3. [Detail View] 선택된 프로젝트 대시보드
    # -----------------------------------------------------
    st.markdown("---")
    
    # [Header] 제목 및 상태
    c_head_1, c_head_2 = st.columns([3, 1])
    with c_head_1:
        st.title(f"📄 {data.get('title', '무제')}")
        st.caption(f"**Ver:** {data.get('version', '1.0')} | **Last Updated:** {time.ctime(selected_folder.stat().st_mtime)}")
    with c_head_2:
        # 간단한 상태 배지
        st.info(f"**장르:** {data.get('genre')}")

    # [Dashboard Grid]
    col_left, col_right = st.columns([1.2, 2])

    # --- [Left Column] 분석 및 컨트롤 ---
    with col_left:
        with st.container(border=True):
            st.subheader("📊 IP 파워 분석")
            if HAS_PLOTLY:
                fig = draw_radar_chart(data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.metric("종합 점수", "분석 중...")
            
            # [Core Stats]
            s1, s2 = st.columns(2)
            s1.metric("예상 독자", data.get('target_reader', '전체'))
            s2.metric("키워드 수", len(data.get('keywords', [])))

        # [Action Center] 제어판
        st.markdown("### ⚡ Action Center")
        
        # A. 제작소 투입
        with st.expander("🏭 **제작 스튜디오 투입**", expanded=True):
            slot = st.selectbox("스튜디오 슬롯", [f"Studio {i}" for i in range(1, 11)], key="slot_selector")
            if st.button("🚀 **제작 착수 (Start Production)**", type="primary", use_container_width=True):
                if 'active_projects' not in st.session_state: st.session_state.active_projects = []
                
                if selected_folder.name not in st.session_state.active_projects:
                    st.session_state.active_projects.append(selected_folder.name)
                    st.toast(f"✅ '{data.get('title')}' 제작 승인! ({slot})", icon="🎬")
                    time.sleep(1)
                else:
                    st.warning("이미 제작 중인 프로젝트입니다.")

        # B. 리메이크 (Develop)
        with st.expander("🛠️ **기획 디벨롭 (Remake)**"):
            req_text = st.text_area("수정 지시사항 (Feedback)", placeholder="예: 주인공 성격을 더 사악하게 바꿔줘.")
            if st.button("✨ **AI 수정 실행**", use_container_width=True):
                if not engine:
                    st.error("엔진 없음")
                else:
                    with st.status("🧠 **기획자가 문서를 수정하고 있습니다...**", expanded=True) as status:
                        new_p, msg = engine.remake_planning(data, req_text)
                        if "Success" in msg:
                            utils.create_new_version(selected_folder, new_p)
                            status.update(label="✅ **수정 완료! (vUp)**", state="complete")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(f"오류: {msg}")

        # C. 폐기
        if st.button("🗑️ **프로젝트 영구 삭제**"):
            utils.delete_project(selected_folder)
            st.toast("삭제되었습니다.")
            time.sleep(1)
            st.rerun()

    # --- [Right Column] 문서 내용 ---
    with col_right:
        # 탭 뷰로 상세 내용 표시
        tab1, tab2, tab3 = st.tabs(["📜 **시놉시스 & 플롯**", "👥 **캐릭터 & 세계관**", "⚔️ **전략 (SWOT)**"])
        
        with tab1:
            st.markdown("#### 📝 로그라인")
            st.info(data.get('logline'))
            
            st.markdown("#### 🎬 시놉시스")
            st.write(data.get('synopsis'))
            
            st.divider()
            st.markdown("#### 📅 회차별 전개")
            for p in data.get('episode_plots', []):
                with st.expander(f"**[{p.get('ep')}화]** {p.get('title')}"):
                    st.write(p.get('summary'))

        with tab2:
            st.markdown("#### 👥 등장인물 리스트")
            for c in data.get('characters', []):
                role = c.get('role', 'Extra')
                emoji = "👑" if "Main" in role else "⚔️" if "Antagonist" in role else "👤"
                st.markdown(f"**{emoji} {c.get('name')}** _({role})_")
                st.caption(c.get('desc'))
                st.markdown("---")
            
            st.markdown("#### 🌍 세계관 설정")
            st.write(data.get('world_view'))

        with tab3:
            swot = data.get('swot_analysis', {})
            c_s, c_w = st.columns(2)
            c_s.success(f"**강점 (Strength)**\n\n{swot.get('strength', '-')}")
            c_w.error(f"**약점 (Weakness)**\n\n{swot.get('weakness', '-')}")
            
            c_o, c_t = st.columns(2)
            c_o.info(f"**기회 (Opportunity)**\n\n{swot.get('opportunity', '-')}")
            c_t.warning(f"**위협 (Threat)**\n\n{swot.get('threat', '-')}")
            
            st.divider()
            st.markdown("#### 💰 세일즈 포인트")
            for sp in data.get('sales_points', []):
                st.markdown(f"✅ {sp}")