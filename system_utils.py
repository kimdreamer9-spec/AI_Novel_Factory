import json
import re
import shutil
from pathlib import Path

# =========================================================
# 🛠️ System Utils (공통 행정실)
# =========================================================

def get_latest_plan_file(folder_path):
    """가장 최신 버전의 기획안 파일을 찾습니다."""
    # v1, v2... 파일 찾기
    v_files = list(folder_path.glob("Approved_Plan_v*.json"))
    if v_files:
        v_files.sort(key=lambda x: int(re.search(r'v(\d+)', x.name).group(1)), reverse=True)
        return v_files[0]

    # 오리지널 파일
    original = folder_path / "Approved_Plan.json"
    if original.exists(): return original

    # 구형 드래프트
    drafts = list(folder_path.glob("기획안_Draft*.json"))
    if drafts:
        drafts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return drafts[0]
    
    return None

def load_project_data(folder_path):
    """프로젝트 폴더에서 데이터를 안전하게 로드합니다."""
    target_file = get_latest_plan_file(folder_path)
    
    if target_file:
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: raise ValueError("Empty File") # 빈 파일 처리
                data = json.loads(content)
                
                # 구형 데이터 호환 처리
                if '1_작품_기본_정보' in data:
                    flat = {}
                    info = data.get('1_작품_기본_정보', {})
                    flat['title'] = info.get('제목', folder_path.name)
                    flat['genre'] = info.get('장르', '미상')
                    flat['logline'] = data.get('3_작품_소개_로그라인', '로그라인 없음')
                    flat['synopsis'] = "구형 데이터입니다. 리메이크를 권장합니다."
                    flat['characters'] = []
                    flat['version'] = "Old"
                    return flat
                
                data['version'] = target_file.name # 버전 정보 주입
                return data
        except Exception as e:
            return {
                "title": folder_path.name,
                "logline": f"❌ 데이터 손상: {str(e)}",
                "genre": "Error",
                "synopsis": "파일을 읽을 수 없습니다. [리메이크] 버튼을 눌러 복구하십시오.",
                "is_corrupted": True,
                "characters": []
            }
            
    return {"title": folder_path.name, "logline": "데이터 파일 없음", "genre": "Empty", "is_corrupted": True}

def create_new_version(folder_path, new_plan_data):
    """새 버전(v+1)으로 저장합니다."""
    try:
        latest = get_latest_plan_file(folder_path)
        next_v = 1
        if latest:
            match = re.search(r'v(\d+)', latest.name)
            if match: next_v = int(match.group(1)) + 1
            elif latest.name == "Approved_Plan.json": next_v = 2
            
        new_name = f"Approved_Plan_v{next_v}.json"
        (folder_path / new_name).write_text(json.dumps(new_plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True, f"v{next_v} 업데이트 완료"
    except Exception as e:
        return False, str(e)

def delete_project(folder_path):
    try:
        shutil.rmtree(folder_path)
        return True
    except: return False