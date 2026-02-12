import streamlit as st
import sys
import pandas as pd
import plotly.express as px
from pathlib import Path

# 루트 경로 설정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

import system_utils as utils
import strategy_judge as engine

def draw_radar_chart(plan_data):
    """기획안의 5각 능력치(육각형) 그래프 생성"""
    # 데이터가 없으면 기본값
    stats = plan_data.get('stats', {
        "대중성": 80, "독창성": 70, "캐릭터": 85, "개연성": 75, "확장성": 60
    })
    
    df = pd.DataFrame(dict(
        r=list(stats.values()),
        theta=list(stats.keys())
    ))
    
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B')
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig

def render(planning_dir):
    st.subheader("📊 기획안 데이터 상황실 (Warehouse)")
    
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.info("보관된 데이터가 없습니다.")
        return

    for folder in projs:
        data = utils.load_project_data(folder)
        label = f"📁 {data.get('title')} (Ver: {data.get('version', '1.0')})"
        
        with st.expander(label):
            if data.get('is_corrupted'):
                st.error("데이터 손상됨.")
                continue

            # --- [시각화 대시보드] ---
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.markdown("#### ⚡ 전력 분석 (Power Stats)")
                # 레이더 차트 그리기
                try:
                    fig = draw_radar_chart(data)
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    st.warning("그래프 모듈 로드 실패 (plotly 필요)")
            
            with c2:
                st.markdown("#### 📋 핵심 요약")
                st.info(f"**로그라인:** {data.get('logline')}")
                st.write(f"**장르:** {data.get('genre')} | **타겟:** {data.get('target_reader', '미정')}")
                
                # SWOT 분석 표시 (데이터가 있을 경우)
                swot = data.get('swot_analysis', {})
                if swot:
                    st.markdown("---")
                    s1, s2 = st.columns(2)
                    s1.success(f"**강점(S):** {swot.get('strength', '-')}")
                    s2.error(f"**약점(W):** {swot.get('weakness', '-')}")

            # --- [상세 내용 보기] ---
            st.divider()
            tab_synop, tab_char, tab_plot = st.tabs(["📜 시놉시스", "👥 캐릭터(5인)", "🗺️ 플롯"])
            
            with tab_synop:
                st.write(data.get('synopsis'))
            
            with tab_char:
                for c in data.get('characters', []):
                    with st.container(border=True):
                        st.markdown(f"**{c.get('name')}** ({c.get('role')})")
                        st.caption(c.get('desc'))

            with tab_plot:
                for p in data.get('episode_plots', []):
                    st.write(f"**[{p.get('ep')}화]** {p.get('summary')}")

            # --- [액션 버튼] ---
            st.divider()
            col_act1, col_act2 = st.columns([1, 1])
            
            with col_act1:
                # 리메이크 (객관적 분석 포함)
                with st.popover("🛠️ 리메이크 요청 (Analyst Mode)"):
                    st.write("사장님의 지시를 **객관적으로 분석**한 후 수정을 진행합니다.")
                    req = st.text_area("수정 지시사항", key=f"req_{folder.name}", placeholder="예: 주인공을 더 악랄하게 바꿔줘.")
                    
                    if st.button("분석 및 수정 실행", key=f"do_{folder.name}", type="primary"):
                        with st.spinner("지시사항의 리스크를 분석하고 있습니다..."):
                            ctx = f"Original Title: {data.get('title')}"
                            # 리메이크 실행 (분석 포함)
                            new_p, logs = engine.process_planning(2, ctx, feedback_history=req)
                            
                            # 분석 결과 먼저 보여주기
                            if new_p.get('remake_analysis'):
                                ra = new_p['remake_analysis']
                                st.warning(f"**[분석가 경고]**\n장점: {ra.get('pros')}\n단점: {ra.get('cons')}\n결론: {ra.get('verdict')}")
                            
                            utils.create_new_version(folder, new_p)
                            time.sleep(2)
                            st.rerun()

            with col_act2:
                if st.button("🗑️ 폐기", key=f"del_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()