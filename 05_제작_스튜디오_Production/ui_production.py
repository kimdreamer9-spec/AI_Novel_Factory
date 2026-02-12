import streamlit as st
import sys
from pathlib import Path

# 경로 설정
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))
import system_utils as utils

try:
    import treatment_writer
    import main_writer
except ImportError:
    treatment_writer = None
    main_writer = None

def render_production_tab(planning_dir, production_dir):
    st.subheader("🏭 실시간 제작 현황")
    
    if not treatment_writer:
        st.error("작가 모듈(treatment_writer, main_writer)이 없습니다. 파일명을 확인하세요.")
        return

    active = st.session_state.get('active_projects', [])
    if not active:
        st.info("대기 중 (창고에서 투입해주세요)")
    else:
        tabs = st.tabs([n.split('_')[-1][:8] for n in active])
        
        for i, pname in enumerate(active):
            with tabs[i]:
                path = planning_dir / pname
                d = utils.load_project_data(path)
                
                # 상태 키 관리
                k_treat = f"treat_{pname}"
                k_main = f"main_{pname}"
                if k_treat not in st.session_state: st.session_state[k_treat] = ""
                if k_main not in st.session_state: st.session_state[k_main] = ""

                st.markdown(f"### 🎬 {d.get('title')}")
                
                c1, c2 = st.columns([1, 1])
                
                # 1단계: 트리트먼트
                with c1:
                    st.info("Step 1. 트리트먼트")
                    if st.button("🏗️ 생성", key=f"btn_t_{pname}"):
                        with st.spinner("플롯 설계 중..."):
                            res = treatment_writer.generate_treatment(d)
                            st.session_state[k_treat] = res
                            st.rerun()
                    
                    txt_treat = st.text_area("설계도", value=st.session_state[k_treat], height=400, key=f"txt_t_{pname}")
                    st.session_state[k_treat] = txt_treat

                # 2단계: 본문
                with c2:
                    st.info("Step 2. 본문 집필")
                    if st.button("✍️ 집필", key=f"btn_w_{pname}", type="primary"):
                        if not st.session_state[k_treat]: st.error("트리트먼트가 필요합니다.")
                        else:
                            with st.spinner("집필 중..."):
                                res = main_writer.write_episode(d, st.session_state[k_treat])
                                st.session_state[k_main] = res
                                st.rerun()
                                
                    txt_main = st.text_area("원고", value=st.session_state[k_main], height=400, key=f"txt_m_{pname}")
                    st.session_state[k_main] = txt_main

                if st.button("⏹️ 중단", key=f"stop_{pname}"):
                    st.session_state.active_projects.remove(pname)
                    st.rerun()