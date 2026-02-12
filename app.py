import streamlit as st
import sys
import time
import json
import os
import shutil
import re
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V15 (Full Pipeline: Plan -> Treat -> Write)
# =========================================================

# 1. 경로 설정
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

# 경로 추가
sys.path.append(str(planning_dir))
sys.path.append(str(production_dir)) # 제작소 모듈 경로 추가

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 엔진 로드
try:
    import strategy_judge as engine
    engine.init_engine()
    ENGINE_STATUS = "🟢 엔진 정상"
    MODEL_INFO = getattr(engine, 'MODEL_NAME', 'Unknown')
except ImportError:
    ENGINE_STATUS = "🔴 엔진 연결 실패"
    MODEL_INFO = "Unknown"

# 제작소 모듈 로드 (지연 로딩)
try:
    import treatment_writer
    import main_writer
    WRITER_STATUS = "🟢 작가 대기 중"
except ImportError:
    WRITER_STATUS = "🔴 작가 모듈 없음"

# --- [UI Component: 7단계 뷰어] ---
def render_plan_report(plan):
    analysis = plan.get('strategy_analysis', {})
    if analysis:
        with st.expander("📊 전략기획실 분석 리포트", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 2])
            c1.metric("트렌드 점수", f"{analysis.get('trend_score', 0)}점")
            c2.info(f"**분석:** {analysis.get('trend_comment', '-')}")
            c3.error(f"**경고:** {analysis.get('red_team_warning', '-')}")

    st.markdown(f"## 📑 {plan.get('title', '제목 미정')}")
    c1, c2 = st.columns(2)
    c1.markdown(f"**장르:** {plan.get('genre')} | **타겟:** {plan.get('target_reader')}")
    c2.markdown(f"**키워드:** {plan.get('keywords')}")
    
    st.info(f"**로그라인:** {plan.get('logline')}")
    
    with st.expander("상세 내용 (시놉시스 & 캐릭터)", expanded=False):
        st.write(f"**기획의도:** {plan.get('planning_intent')}")
        st.write(f"**시놉시스:** {plan.get('synopsis')}")
        st.json(plan.get('characters'))

# --- [Logic Functions] ---
def get_latest_plan_file(folder_path):
    v_files = list(folder_path.glob("Approved_Plan_v*.json"))
    if v_files:
        v_files.sort(key=lambda x: int(re.search(r'v(\d+)', x.name).group(1)), reverse=True)
        return v_files[0]
    orig = folder_path / "Approved_Plan.json"
    if orig.exists(): return orig
    drafts = list(folder_path.glob("기획안_Draft*.json"))
    if drafts:
        drafts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return drafts[0]
    return None

def load_project_data(folder_path):
    target = get_latest_plan_file(folder_path)
    if target:
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: raise ValueError
                data = json.loads(content)
                if '1_작품_기본_정보' in data: # 구형
                    return {'title': data.get('1_작품_기본_정보', {}).get('제목', folder_path.name), 'version': 'Old'}
                data['version'] = target.name
                return data
        except: pass
    return {"title": folder_path.name, "is_corrupted": True}

def create_new_version(folder_path, new_data):
    try:
        latest = get_latest_plan_file(folder_path)
        next_v = 1
        if latest:
            match = re.search(r'v(\d+)', latest.name)
            if match: next_v = int(match.group(1)) + 1
            elif latest.name == "Approved_Plan.json": next_v = 2
        (folder_path / f"Approved_Plan_v{next_v}.json").write_text(json.dumps(new_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True, f"v{next_v} 저장됨"
    except Exception as e: return False, str(e)

def move_to_production(project_name):
    if 'active_projects' not in st.session_state: st.session_state.active_projects = []
    if project_name not in st.session_state.active_projects:
        st.session_state.active_projects.append(project_name)

def delete_project(folder_path):
    try: shutil.rmtree(folder_path); return True
    except: return False

# 4. Main App
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"Engine: {ENGINE_STATUS} ({MODEL_INFO}) | Writer: {WRITER_STATUS}")

if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

tab1, tab2, tab3, tab4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소", "⚖️ 4. 품질관리"])

# --- Tab 1: 기획실 ---
with tab1:
    st.subheader("🧠 신규 기획 생성")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.info("🛠️ 작전 지시")
        mode = st.radio("모드", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        u_input = st.text_area("키워드 / 아이디어", height=150)
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "🔴" in ENGINE_STATUS: st.error("엔진 오류")
            else:
                with st.spinner("PD가 7단계 표준 기획안 작성 중..."):
                    m = int(mode[0])
                    res, logs = engine.process_planning(m, u_input)
                    st.session_state.current_plan = res
                    st.rerun()
    with c2:
        if st.session_state.current_plan:
            render_plan_report(st.session_state.current_plan)
            b1, b2 = st.columns(2)
            if b1.button("💾 승인 및 입고"):
                succ, msg = engine.save_and_deploy(st.session_state.current_plan)
                if succ:
                    st.toast("저장 완료!", icon="📦")
                    st.session_state.current_plan = None
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
            if b2.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()

# --- Tab 2: 창고 ---
with tab2:
    st.subheader("📦 기획안 보관소")
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs: st.warning("데이터 없음")
    else:
        for folder in projs:
            data = load_project_data(folder)
            label = f"📁 {data.get('title')} ({folder.name})"
            if data.get('is_corrupted'): label = f"❌ [손상됨] {folder.name}"
            
            with st.expander(label):
                if data.get('is_corrupted'):
                    st.error("데이터 손상됨. 복구 필요.")
                else:
                    render_plan_report(data)

                st.markdown("---")
                c_act, _ = st.columns([1, 1])
                with c_act:
                    if not data.get('is_corrupted'):
                        if folder.name in st.session_state.active_projects:
                            st.success("✅ 제작 중")
                        else:
                            if st.button("🚀 제작 투입", key=f"go_{folder.name}"):
                                move_to_production(folder.name)
                                st.toast("투입 완료!", icon="🔥")
                                st.rerun()
                            
                    with st.popover("🛠️ 리메이크 / 복구"):
                        st.write("내용 수정 또는 **손상된 파일 복구**를 수행합니다.")
                        req = st.text_area("지시사항", key=f"req_{folder.name}")
                        if st.button("수정 실행", key=f"do_{folder.name}", type="primary"):
                            with st.spinner("작업 중..."):
                                ctx = f"제목: {data.get('title')}"
                                new_p, _ = engine.process_planning(2, ctx, feedback_history=req)
                                succ, msg = create_new_version(folder, new_p)
                                if succ:
                                    st.success("완료")
                                    time.sleep(1)
                                    st.rerun()
                                else: st.error(msg)
                    
                    if st.button("🗑️ 삭제", key=f"del_{folder.name}"):
                        delete_project(folder)
                        st.rerun()

# --- Tab 3: 제작소 ---
with tab3:
    st.subheader("🏭 실시간 제작 현황")
    active = st.session_state.active_projects
    if not active: st.info("대기 중 (창고에서 투입해주세요)")
    else:
        tabs = st.tabs([n.split('_')[-1][:8] for n in active])
        for i, pname in enumerate(active):
            with tabs[i]:
                path = planning_dir / pname
                d = load_project_data(path)
                
                # 상태 키 (트리트먼트 & 본문)
                k_treat = f"treat_{pname}"
                k_main = f"main_{pname}"
                if k_treat not in st.session_state: st.session_state[k_treat] = ""
                if k_main not in st.session_state: st.session_state[k_main] = ""

                st.markdown(f"### 🎬 {d.get('title')}")
                
                c1, c2 = st.columns([1, 1])
                
                # 1단계: 트리트먼트
                with c1:
                    st.info("Step 1. 트리트먼트 (설계)")
                    if st.button("🏗️ 트리트먼트 생성", key=f"btn_t_{pname}"):
                        with st.spinner("플롯 설계 중..."):
                            res = treatment_writer.generate_treatment(d)
                            st.session_state[k_treat] = res
                            st.rerun()
                    
                    txt_treat = st.text_area("설계도 내용", value=st.session_state[k_treat], height=400, key=f"txt_t_{pname}")
                    st.session_state[k_treat] = txt_treat

                # 2단계: 본문
                with c2:
                    st.info("Step 2. 본문 집필 (생산)")
                    if st.button("✍️ 본문 집필 시작", key=f"btn_w_{pname}", type="primary"):
                        if not st.session_state[k_treat]: st.error("트리트먼트 먼저!")
                        else:
                            with st.spinner("집필 중..."):
                                res = main_writer.write_episode(d, st.session_state[k_treat])
                                st.session_state[k_main] = res
                                st.balloons()
                                st.rerun()
                                
                    txt_main = st.text_area("원고 내용", value=st.session_state[k_main], height=400, key=f"txt_m_{pname}")
                    st.session_state[k_main] = txt_main

                if st.button("💾 파일 저장", key=f"save_{pname}"):
                    # 파일 저장 로직 (production 폴더에)
                    save_path = production_dir / pname
                    save_path.mkdir(parents=True, exist_ok=True)
                    (save_path / "Ep1_Treatment.md").write_text(st.session_state[k_treat], encoding='utf-8')
                    (save_path / "Ep1_Main.txt").write_text(st.session_state[k_main], encoding='utf-8')
                    st.success(f"저장됨: {save_path}")

                if st.button("⏹️ 중단 (목록 제거)", key=f"stop_{pname}"):
                    st.session_state.active_projects.remove(pname)
                    st.rerun()

with tab4: st.info("QC 대기")