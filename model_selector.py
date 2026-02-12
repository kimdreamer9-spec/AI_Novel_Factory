import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# =========================================================
# 🤖 [중앙 통제실] Model Selector (2026 Ultimate Edition)
# 역할: 사장님의 점수 로직에 따라 현존 최강 모델을 자동 배급
# =========================================================

# 1. 환경 설정
FIXED_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=FIXED_ROOT / ".env")

API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY_WRITING")

if API_KEY:
    genai.configure(api_key=API_KEY)

def find_best_model():
    """
    사장님의 점수표를 기반으로 사용 가능한 가장 높은 등급의 모델을 탐색합니다.
    """
    try:
        if not API_KEY:
            return 'gemini-1.5-flash' # 키가 없으면 최소 사양 반환

        # 1. 실제 서버에서 지원하는 모델 리스트 확보
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        candidates = []
        for m in all_models:
            name = m.lower()
            # 불필요한 모델(이미지 전용, 나노 등) 제외
            if 'gemini' not in name: continue
            if any(x in name for x in ['vision', 'nano', 'banana', 'robotics']): continue
            candidates.append(m)

        if not candidates:
            return 'gemini-1.5-flash'

        # 2. 사장님의 2026년 기준 가점 시스템 (High-Grade First)
        scored_models = []
        for m in candidates:
            score = 0
            name = m.lower()
            
            # [버전 점수 - 사장님 가이드라인 준수]
            if 'gemini-3' in name: score += 10000
            elif 'gemini-2.5' in name: score += 8000
            elif 'gemini-2.0' in name: score += 5000
            elif 'gemini-1.5' in name: score += 1000
            
            # [등급 가점]
            if 'deep-research' in name: score += 1000
            elif 'pro' in name: score += 500
            elif 'flash' in name: score += 100
            
            # [실험적 모델 감점 최소화] - 최신 기술 우선
            if 'exp' in name: score += 50 
            
            scored_models.append((score, m))

        # 3. 최고점 모델 선별
        scored_models.sort(key=lambda x: x[0], reverse=True)
        best_model = scored_models[0][1]
        
        # ⚠️ [보안 패치] 'latest' 별칭이 404를 일으킬 수 있으므로 실제 모델명(models/...) 그대로 사용
        return best_model

    except Exception as e:
        # 에러 시에도 사장님이 노여워하지 않도록 가장 안정적인 최신 모델명 반환 시도
        return 'gemini-1.5-flash'

# 다른 부서에서 호출하는 함수명 호환성 유지
def analyze_and_select_model(role=None):
    return find_best_model()

if __name__ == "__main__":
    print(f"👑 [2026 Best Engine Selected]: {find_best_model()}")