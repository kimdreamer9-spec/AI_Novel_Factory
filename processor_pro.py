import os
import re
import json
import time
import warnings
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# ⚙️ [가공 팀] Processor Pro (Pure OCR Edition)
# 역할: 이미지 -> 텍스트 변환 -> 화수 분할 (분석 기능 제거됨)
# =========================================================

warnings.filterwarnings("ignore")
load_dotenv()

# 1. API 키 확인
API_KEY = os.getenv("GEMINI_KEY_PLANNING")
if not API_KEY:
    print("❌ [오류] .env 파일에서 API 키를 찾을 수 없습니다.")
    exit()

genai.configure(api_key=API_KEY)

# ---------------------------------------------------------
# 🤖 [엔진 자동 배차] 복잡한 모델명 고민 끝. 되는 거 알아서 잡음.
# ---------------------------------------------------------
def auto_select_model():
    print("\n🔍 [시스템] 사용 가능한 AI 엔진을 탐색합니다...")
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                available_models.append(name)
        
        # 우선순위: Pro(고성능) > Flash(고속) > 아무거나
        best_model = None
        
        # 1. Pro 계열 탐색 (정확도 최우선)
        for m in available_models:
            if 'pro' in m.lower() and 'vision' not in m.lower(): # vision 전용 제외
                 best_model = m
                 break
        
        # 2. 없으면 Flash 계열
        if not best_model:
            for m in available_models:
                if 'flash' in m.lower():
                    best_model = m
                    break
                    
        # 3. 정 없으면 목록의 첫 번째
        if not best_model and available_models:
            best_model = available_models[0]
            
        if not best_model:
             print("❌ [치명적 오류] 사용 가능한 모델이 없습니다.")
             exit()

        print(f"   ✅ [엔진 확정] '{best_model}' 모델로 가동합니다.")
        return genai.GenerativeModel(best_model)

    except Exception as e:
        print(f"❌ [치명적 오류] 모델 목록 조회 실패: {e}")
        exit()

# 엔진 시동
model = auto_select_model()
BASE_DIR = Path.cwd()

# 감시 경로 설정
REALTIME_ROOT = BASE_DIR / "99_실시간_작업방"
MANUAL_ROOT = BASE_DIR / "01_자료실_Raw_Data"
OUTPUT_ROOT = BASE_DIR / "01_자료실_Raw_Data" / "00_성공작_아카이브"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]

def ocr_images(image_paths, novel_title):
    full_text = ""
    total_imgs = len(image_paths)
    print(f"      📸 [OCR] 이미지 {total_imgs}장 변환 시작...")
    
    batch_size = 10
    for i in range(0, total_imgs, batch_size):
        batch = image_paths[i:i+batch_size]
        
        # [프롬프트] 오직 텍스트 추출에만 집중
        prompt = """
        이미지의 소설 내용을 텍스트로만 추출해.
        [절대 규칙]
        1. '< 001 : 제목 >' 같은 회차 구분자는 원본 그대로 유지할 것.
        2. UI, 시간, 배터리 같은 잡다한 정보는 삭제할 것.
        3. 분석하지 말고 있는 그대로 글자만 옮길 것.
        """
        
        try:
            img_objects = []
            for img_path in batch:
                img_data = Path(img_path).read_bytes()
                img_objects.append({'mime_type': 'image/png', 'data': img_data})
            
            # 타임아웃 넉넉하게
            response = model.generate_content([prompt, *img_objects], request_options={'timeout': 90})
            if response.text:
                full_text += response.text + "\n\n"
            
            print(f"         ... {min(i+batch_size, total_imgs)}/{total_imgs} 완료")
            time.sleep(1) # API 보호
            
        except Exception as e:
            print(f"      🚨 변환 실패(구간 {i}): {e}")
            
    return full_text

def split_episodes(full_text, novel_title):
    # <...>, [...] 패턴으로 회차 나누기
    split_pattern = r"(?:<|\[)[^>\]]*(?:\d+|화|프롤로그|에필로그)[^>\]]*(?:>|\])"
    matches = list(re.finditer(split_pattern, full_text))
    
    if not matches:
        # 구분자 없으면 통파일 1개 생성
        return [(f"{novel_title}_통합본.md", full_text)]

    results = []
    for i in range(len(matches)):
        start_idx = matches[i].start()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
        
        chunk = full_text[start_idx:end_idx].strip()
        
        # 파일명 생성 (특수문자 제거)
        title_raw = matches[i].group().strip()
        safe_title = re.sub(r'[\\/*?:"<>|\[\]]', "", title_raw).strip()
        filename = f"{novel_title}_{i+1:03d}_{safe_title}.md"
        results.append((filename, chunk))
        
    return results

def process_novels():
    print("\n🏭 [공장 가동] 단순 가공 모드 (OCR -> MD)")
    
    target_dirs = []

    # 1. 실시간 작업방 (SCAN_COMPLETE 파일 확인)
    if REALTIME_ROOT.exists():
        for d in REALTIME_ROOT.iterdir():
            if d.is_dir() and (d / "SCAN_COMPLETE").exists():
                print(f"⚡ [대기열] 실시간 스캔본: {d.name}")
                target_dirs.append(d)

    # 2. 수동 투입구 (99_로 시작하는 폴더 확인)
    if MANUAL_ROOT.exists():
        for d in MANUAL_ROOT.iterdir():
            if d.is_dir() and d.name.startswith("99_"):
                for sub_d in d.iterdir():
                    if sub_d.is_dir():
                        target_dirs.append(sub_d)

    if not target_dirs:
        print("❌ 처리할 파일이 없습니다.")
        return

    for novel_dir in target_dirs:
        print(f"\n📘 [작업 시작] {novel_dir.name}")
        
        images = []
        for ext in ["*.png", "*.jpg", "*.jpeg", "*.ZK", "*.zk"]:
            images.extend(list(novel_dir.glob(ext)))
            images.extend(list(novel_dir.glob(ext.upper())))
        images.sort(key=natural_sort_key)
        
        if not images:
            print(f"      ⚠️ 폴더가 비어있습니다.")
            continue
        
        # [변경] 장르 분석 API 제거 -> 스캐너가 준 파일 쓰거나 '수동' 처리
        genre = "미분류_수동"
        if (novel_dir / "genre.txt").exists():
            genre = (novel_dir / "genre.txt").read_text(encoding='utf-8').strip()
            # 번호표 제거 (01_재벌물 -> 재벌물)
            genre = genre.split("_")[-1] if "_" in genre else genre
        
        print(f"      🏷️ 분류: {genre}")

        # 1. OCR 실행
        text = ocr_images(images, novel_dir.name)
        if not text: continue

        # 2. 쪼개기
        episodes = split_episodes(text, novel_dir.name)
        
        # 3. 저장
        save_dir = OUTPUT_ROOT / genre / novel_dir.name
        save_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"      💾 저장 중... ({len(episodes)}개 파일)")
        for fname, content in episodes:
            (save_dir / fname).write_text(content, encoding='utf-8')
        
        # 메타 정보 껍데기 (나중에 채울 용도)
        if not (save_dir / f"{novel_dir.name}_meta.json").exists():
            (save_dir / f"{novel_dir.name}_meta.json").write_text(
                json.dumps({"title": novel_dir.name, "genre": genre}, indent=4, ensure_ascii=False), encoding='utf-8'
            )

        # 실시간 작업방 정리 (이름 변경)
        if "99_실시간_작업방" in str(novel_dir):
            try:
                novel_dir.rename(novel_dir.parent / f"_DONE_{novel_dir.name}")
                print("      🧹 작업 완료 태그 부착")
            except: pass
            
        print("      ✅ 완료")

    print("\n🎉 모든 변환 작업 끝.")

if __name__ == "__main__":
    process_novels()