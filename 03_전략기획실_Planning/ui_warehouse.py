import streamlit as st
import sys
import time
import pandas as pd
from pathlib import Path

# =========================================================
# 🏗️ [Path Safety] 경로 고속도로 (Path Fix)
# =========================================================
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(current_dir) not in sys.path: sys.path.append(str(current_dir))
if str(root_dir) not in sys.path: sys.path.append(str(root_dir))

import system_utils as utils
try:
    import strategy_judge as engine
except ImportError:
    engine = None

# 🔥 [Plotly Safety] 그래프 엔진 점검
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

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
            radialaxis=dict(visible=True, range=[0, 100]),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig

def render(planning_dir):
    st.markdown("## 🗂️ 기획 창고 (Project Warehouse)")
    st.caption("📦 저장된 기획안 관리 • 🏭 제작소 투입 • 🛠️ 리메이크(Develop)")

    if not HAS_PLOTLY:
        st.warning("⚠️ `pip install plotly`를 설치하면 육각형 능력치 그래프를 볼 수 있습니다.")

    # 1. 파일 스캔
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.info("📭 보관된 기획안이 없습니다. [전략기획실]에서 기획을 생성하세요.")
        return

    # 2. 프로젝트 리스트 렌더링
    for folder in projs:
        data = utils.load_project_data(folder)
        label = f"📁 {data.get('title', '무제')} (v{data.get('version', '1.0')})"
        
        # 손상된 파일 처리
        if data.get('is_corrupted'):
            with st.expander(f"❌ [손상됨] {folder.name}"):
                st.error("데이터가 손상되었습니다.")
                if st.button("영구 삭제", key=f"del_corrupt_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()
            continue

        # 정상 파일 렌더링
        with st.expander(label, expanded=False):
            # --- [Part 1: 대시보드] ---
            c1, c2 = st.columns([1, 1.5])
            
            with c1:
                st.markdown("##### ⚡ 전력 분석 (Radar)")
                if HAS_PLOTLY:
                    fig = draw_radar_chart(data)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.progress(data.get('stats', {}).get('대중성', 50) / 100)
                    st.caption("그래프 엔진 없음 (수치로 대체)")
            
            with c2:
                st.markdown("##### 📋 핵심 요약")
                st.info(f"**로그라인:** {data.get('logline')}")
                st.caption(f"장르: {data.get('genre')} | 타겟: {data.get('target_reader', '전체')}")
                
                # SWOT (데이터 있으면)
                swot = data.get('swot_analysis', {})
                if swot:
                    s_col, w_col = st.columns(2)
                    s_col.success(f"**강점:** {swot.get('strength', '-')}")
                    w_col.error(f"**약점:** {swot.get('weakness', '-')}")

            st.divider()

            # --- [Part 2: 상세 내용 (탭 뷰어)] ---
            t1, t2, t3, t4 = st.tabs(["📜 시놉시스", "👥 캐릭터(5인)", "🗺️ 플롯(1-5화)", "💡 포인트"])
            
            with t1:
                st.write(data.get('synopsis'))
            
            with t2:
                for char in data.get('characters', []):
                    with st.container(border=True):
                        st.markdown(f"**{char.get('name')}** ({char.get('role')})")
                        st.caption(f"MBTI: {char.get('mbti', '-')} | {char.get('desc')}")
            
            with t3:
                for plot in data.get('episode_plots', []):
                    st.markdown(f"**[{plot.get('ep')}화] {plot.get('title')}**")
                    st.caption(plot.get('summary'))

            with t4:
                for sp in data.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

            st.divider()

            # --- [Part 3: 액션 컨트롤 (제작/수정/삭제)] ---
            col_prod, col_dev, col_del = st.columns([2, 2, 1])
            
            # [A] 제작소 투입 (슬롯 시스템)
            with col_prod:
                with st.popover("🚀 제작 투입 (Send to Studio)"):
                    st.write("작업할 스튜디오(슬롯)를 선택하세요.")
                    # 세션 상태에서 활성 슬롯 확인
                    active_slots = st.session_state.get('active_projects', [])
                    
                    # 1~10번 슬롯 생성
                    slot_options = []
                    for i in range(1, 11):
                        status = "🟢 빈 슬롯"
                        # (간단 구현) 실제로는 슬롯별 매핑이 필요하나, 여기선 리스트 존재 여부로 체크
                        # 고도화를 위해선 딕셔너리 관리가 필요함. 일단 리스트 추가 방식.
                        slot_options.append(f"Studio {i}")

                    selected_slot = st.selectbox("스튜디오 선택", slot_options)
                    
                    if st.button("제작 시작", key=f"go_{folder.name}", type="primary"):
                        if 'active_projects' not in st.session_state:
                            st.session_state.active_projects = []
                        
                        # 중복 체크
                        if folder.name in st.session_state.active_projects:
                            st.warning("이미 제작 중인 프로젝트입니다.")
                        else:
                            st.session_state.active_projects.append(folder.name)
                            st.toast(f"'{data.get('title')}' 작품이 {selected_slot}에 투입되었습니다!", icon="🏭")
                            time.sleep(1)
            
            # [B] 디벨롭 (스마트 리메이크)
            with col_dev:
                with st.popover("🛠️ 디벨롭 (Smart Remake)"):
                    st.markdown("### 👨‍🏫 수석 기획자(Analyst) 대화")
                    st.caption("단순한 수정이 아닙니다. 사장님의 지시를 상업적으로 분석하여 경고하거나 추천합니다.")
                    
                    req = st.text_area("수정 지시사항 (Prompt)", key=f"req_{folder.name}", placeholder="예: 주인공 성격을 더 사이코패스처럼 바꿔줘. 근데 로맨스는 유지해.")
                    
                    if st.button("분석 및 수정 실행", key=f"do_{folder.name}"):
                        if not engine:
                            st.error("기획 엔진이 로드되지 않았습니다.")
                        else:
                            with st.status("🕵️ **지시사항을 분석 중입니다...**") as status:
                                ctx = f"Original Title: {data.get('title')}\nOriginal Synopsis: {data.get('synopsis')[:200]}"
                                
                                # Mode 2: 유저 기획 디벨롭 (리메이크)
                                new_p, logs = engine.process_planning(2, ctx, feedback_history=req)
                                
                                # 분석 결과 표시 (Strategy Judge가 remake_analysis를 줌)
                                if new_p.get('remake_analysis'):
                                    ra = new_p['remake_analysis']
                                    st.info(f"**[분석 결과]**\n👍 장점: {ra.get('pros')}\n👎 위험: {ra.get('cons')}\n⚖️ 판단: {ra.get('verdict')}")
                                
                                status.update(label="수정 완료! 새로운 버전으로 저장합니다.", state="complete")
                                
                                # 새 버전 저장
                                utils.create_new_version(folder, new_p)
                                time.sleep(2)
                                st.rerun()

            # [C] 폐기
            with col_del:
                if st.button("🗑️ 폐기", key=f"del_{folder.name}"):
                    utils.delete_project(folder)
                    st.toast("프로젝트가 영구 삭제되었습니다.")
                    time.sleep(1)
                    st.rerun()