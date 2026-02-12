import streamlit as st
import sys
import time
import json
import os
import shutil
import re
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V13 (Strategic Analysis UI)
# =========================================================

# 1. 경로 설정
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

if str(planning_dir) not in sys.path:
    sys.path.append(str(planning_dir))

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

# --- [UI Component: 표준 보고서 뷰어] ---
def render_plan_report(plan):
    """사장님 표준 7단계 기획안 + 전략 분석 리포트"""
    
    # 0. 전략 분석 리포트 (최상단 배치)
    analysis = plan.get('strategy_analysis', {})
    if analysis:
        with st.expander("📊 전략기획실 분석 리포트 (Cold Review)", expanded=True):
            cols = st.columns([1, 2, 2])
            with cols[0]:
                score = analysis.get('trend_score', 0)
                st.metric("트렌드 적합도", f"{score}점")
            with cols[1]:
                st.info(f"**📈 트렌드 분석:**\n{analysis.get('trend_comment', '-')}")
                st.success(f"**✅ 루브릭 평가:**\n{analysis.get('rubric_evaluation', '-')}")
            with cols[2]:
                st.error(f"**👺 Red Team 경고:**\n{analysis.get('red_team_warning', '-')}")
                st.warning(f"**💡 개선 제안:**\n{analysis.get('improvement_suggestion', '-')}")

    # 1. 헤더
    st.markdown(f"## 📑 {plan.get('title', '제목 미정')}")
    
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        st.markdown(f"**🏷️ 장르:** {plan.get('genre', '미정')}")
        st.markdown(f"**🎯 타겟 독자:** {plan.get('target_reader', '미정')}")
    with col_meta2:
        keywords = plan.get('keywords', [])
        kw_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        st.markdown(f"**🔑 키워드:** {kw_str}")

    # 2. 기획의도
    with st.container(border=True):
        st.markdown("### 💡 2. 기획 의도 및 셀링 포인트")
        st.write(f"**기획 의도:** {plan.get('planning_intent', '-')}")
        st.write("**🔥 셀링 포인트:**")
        points = plan.get('selling_points', [])
        if isinstance(points, list):
            for p in points: st.write(f"- {p}")
        else: st.write(points)

    # 3. 로그라인
    st.info(f"**📢 3. 한 줄 소개 (Logline):**\n\n\"{plan.get('logline', '-')}\"")

    # 4. 캐릭터
    with st.expander("👥 4. 캐릭터 설정 (펼치기)", expanded=False):
        chars = plan.get('characters', [])
        if chars:
            for char in chars:
                if isinstance(char, dict):
                    st.markdown(f"**{char.get('name')}** ({char.get('role')}): {char.get('desc')}")
                else: st.write(f"- {char}")
        else: st.write("데이터 없음")

    # 5. 시놉시스
    with st.expander("📜 5. 시놉시스 (전체 줄거리)", expanded=False):
        st.write(plan.get('synopsis', '-'))

    # 6. 전체 구성
    with st.expander("🗺️ 6. 전체 구성 (초/중/후반)", expanded=True):
        comp = plan.get('composition', {})
        if isinstance(comp, dict):
            st.markdown(f"**🔹 초반 (1~25화):** {comp.get('beginning', '-')}")
            st.markdown(f"**🔹 중반 (26~100화):** {comp.get('middle', '-')}")
            st.markdown(f"**🔹 후반 (101화~):** {comp.get('end', '-')}")
        else: st.write(comp)

    # 7. 1화 포인트
    with st.container(border=True):
        st.markdown("### 🎬 7. 1화 핵심 포인트")
        ep1 = plan.get('ep1_core_points', {})
        if isinstance(ep1, dict):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**📌 오프닝:**\n{ep1.get('opening', '-')}")
            c2.markdown(f"**💥 클라이맥스:**\n{ep1.get('climax', '-')}")
            c3.markdown(f"**🎣 엔딩 (절단신):**\n{ep1.get('ending', '-')}")
        else: st.write(ep1)

# 3. Helper Functions (Logic)
def get_latest_plan_file(folder_path):
    versioned_files = list(folder_path.glob("Approved_Plan_v*.json"))
    if versioned_files:
        versioned_files.sort(key=lambda x: int(re.search(r'v(\d+)', x.name).group(1)), reverse=True)
        return versioned_files[0]
    
    original = folder_path / "Approved_Plan.json"
    if original.exists(): return original

    drafts = list(folder_path.glob("기획안_Draft*.json"))
    if drafts:
        drafts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return drafts[0]
    return None

def load_project_data(folder_path):
    target_file = get_latest_plan_file(folder_path)
    if target_file:
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: raise ValueError
                data = json.loads(content)
                if '1_작품_기본_정보' in data: # 구형 호환
                    return {
                        'title': data.get('1_작품_기본_정보', {}).get('제목', folder_path.name),
                        'logline': data.get('3_작품_소개_로그라인', ''),
                        'synopsis': "구형 포맷입니다. 리메이크를 눌러 업데이트하세요.",
                        'version': 'Old'
                    }
                data['version'] = target_file.name
                return data
        except: pass
    return {"title": folder_path.name, "logline": "❌ 데이터 손상 (리메이크 필요)", "genre": "Error"}

def create_new_version(folder_path, new_plan_data):
    try:
        v_files = list(folder_path.glob("Approved_Plan_v*.json"))
        next_v = 1
        if v_files:
            v_nums = [int(re.search(r'v(\d+)', f.name).group(1)) for f in v_files]
            next_v = max(v_nums) + 1
        elif (folder_path / "Approved_Plan.json").exists():
            next_v = 2
        new_name = f"Approved_Plan_v{next_v}.json"
        (folder_path / new_name).write_text(json.dumps(new_plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True, f"v{next_v} 업데이트 완료"
    except Exception as e: return False, str(e)

def move_to_production(project_name):
    if 'active_projects' not in st.session_state: st.session_state.active_projects = []
    if project_name not in st.session_state.active_projects:
        st.session_state.active_projects.append(project_name)

def delete_project(folder_path):
    try: shutil.rmtree(folder_path); return True
    except: return False

# 4. Main UI
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

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
                with st.spinner("PD가 시장 분석 및 전략 수립 중..."):
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
            with st.expander(f"📁 {data.get('title')} ({folder.name})"):
                if data.get('genre') == 'Error' or data.get('version') == 'Old':
                    st.error(data.get('logline'))
                else:
                    render_plan_report(data)

                st.markdown("---")
                c_act, _ = st.columns([1, 1])
                with c_act:
                    if folder.name in st.session_state.active_projects:
                        st.success("✅ 제작 중")
                    else:
                        if st.button("🚀 제작 투입", key=f"go_{folder.name}"):
                            move_to_production(folder.name)
                            st.toast("투입 완료!", icon="🔥")
                            st.rerun()
                            
                    with st.popover("🛠️ 리메이크 (전략 분석 포함)"):
                        st.write("기존 기획을 **트렌드/데이터 기반**으로 재분석하여 수정합니다.")
                        req = st.text_area("수정 지시사항", key=f"req_{folder.name}")
                        if st.button("수정 실행", key=f"do_{folder.name}", type="primary"):
                            with st.spinner("전략기획실이 데이터를 분석하며 수정 중..."):
                                ctx = f"기존 제목: {data.get('title')}\n기존 내용: {data.get('synopsis')}"
                                new_p, _ = engine.process_planning(2, ctx, feedback_history=req)
                                succ, msg = create_new_version(folder, new_p)
                                if succ:
                                    st.success("업데이트 완료")
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
    if not active: st.info("대기 중")
    else:
        tabs = st.tabs([n.split('_')[-1][:8] for n in active])
        for i, pname in enumerate(active):
            with tabs[i]:
                path = planning_dir / pname
                d = load_project_data(path)
                st.markdown(f"### {d.get('title')}")
                
                with st.expander("📚 설정 자료 확인"):
                    render_plan_report(d)
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.info("진행률: 10%")
                    if st.button("⏹️ 중단", key=f"stop_{pname}"):
                        st.session_state.active_projects.remove(pname)
                        st.rerun()
                with c2:
                    st.chat_input("지시 입력...", key=f"chat_{pname}")

with tab4: st.info("QC 대기")