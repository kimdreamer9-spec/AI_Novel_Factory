import streamlit as st
import sys
import pandas as pd
import plotly.express as px
from pathlib import Path

# 루트 경로 설정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

import system_utils as utils
import strategy_judge as engine

def draw_radar_chart(plan_data):
    """
    기획안의 5각 능력치(육각형) 그래프 생성 (Plotly Engine)
    """
    # 데이터가 없으면 랜덤/기본값으로 채워서라도 보여줌 (시각화 보장)
    stats = plan_data.get('stats', {
        "대중성": 80, "독창성": 70, "캐릭터": 85, "개연성": 75, "확장성": 60
    })
    
    df = pd.DataFrame(dict(
        r=list(stats.values()),
        theta=list(stats.keys())
    ))
    
    # 레이더 차트 디자인 (빨간색 테마)
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]),
            bgcolor='rgba(0,0,0,0)' # 투명 배경
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig

def render(planning_dir):
    st.subheader("📊 기획안 데이터 상황실 (Data Command Center)")
    
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.info("보관된 기획안이 없습니다.")
        return

    for folder in projs:
        data = utils.load_project_data(folder)
        label = f"📁 {data.get('title')} (Ver: {data.get('version', '1.0')})"
        
        # 손상된 파일 처리
        if data.get('is_corrupted'):
            with st.expander(f"❌ [손상됨] {folder.name}"):
                st.error("데이터가 손상되었습니다.")
                if st.button("🗑️ 삭제", key=f"del_corrupt_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()
            continue

        # 정상 파일 렌더링
        with st.expander(label):
            # --- [Part 1: 시각화 대시보드] ---
            c1, c2 = st.columns([1, 1.5])
            
            with c1:
                st.markdown("##### ⚡ 전력 분석 (Radar)")
                fig = draw_radar_chart(data)
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.markdown("##### 📋 핵심 요약")
                st.info(f"**로그라인:** {data.get('logline')}")
                st.caption(f"장르: {data.get('genre')} | 타겟: {data.get('target_reader', '전체 이용가')}")
                
                # SWOT 분석 (데이터 존재 시)
                swot = data.get('swot_analysis', {})
                if swot:
                    s_col, w_col = st.columns(2)
                    s_col.success(f"**강점:** {swot.get('strength', '-')}")
                    w_col.error(f"**약점:** {swot.get('weakness', '-')}")

            st.divider()

            # --- [Part 2: 상세 내용 (5단계 표준)] ---
            t1, t2, t3, t4 = st.tabs(["📜 시놉시스", "👥 캐릭터(5인)", "🗺️ 플롯(1-5화)", "💡 포인트"])
            
            with t1:
                st.write(data.get('synopsis'))
            
            with t2:
                for char in data.get('characters', []):
                    with st.container(border=True):
                        st.markdown(f"**{char.get('name')}** ({char.get('role')})")
                        st.caption(f"MBTI: {char.get('mbti', '-')}")
                        st.write(char.get('desc'))
            
            with t3:
                for plot in data.get('episode_plots', []):
                    st.write(f"**[{plot.get('ep')}화] {plot.get('title')}**")
                    st.caption(plot.get('summary'))

            with t4:
                for sp in data.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

            st.divider()

            # --- [Part 3: 액션 버튼 (리메이크/삭제)] ---
            ac1, ac2 = st.columns([2, 1])
            
            with ac1:
                with st.popover("🛠️ 리메이크 요청 (Analyst Mode)"):
                    st.write("사장님의 지시를 **객관적으로 분석**한 후 수정을 진행합니다.")
                    req = st.text_area("수정 지시사항", key=f"req_{folder.name}", placeholder="예: 주인공을 더 악랄하게 바꿔줘.")
                    
                    if st.button("분석 및 수정 실행", key=f"do_{folder.name}", type="primary"):
                        with st.spinner("지시사항의 리스크를 분석하고, 기획안을 재설계 중..."):
                            ctx = f"Original Title: {data.get('title')}"
                            # 리메이크 실행
                            new_p, logs = engine.process_planning(2, ctx, feedback_history=req)
                            
                            # 분석 결과(경고) 먼저 보여주기
                            if new_p.get('remake_analysis'):
                                ra = new_p['remake_analysis']
                                st.warning(f"**[분석가 경고]**\n장점: {ra.get('pros')}\n단점: {ra.get('cons')}\n결론: {ra.get('verdict')}")
                            
                            utils.create_new_version(folder, new_p)
                            time.sleep(2)
                            st.rerun()

            with ac2:
                if st.button("🗑️ 폐기", key=f"del_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()