import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# =========================================================
# 🤖 [중앙 통제실] Model Selector (The Universal Adaptor)
# 위치: 프로젝트 최상위 루트 (Root)
# 역할: 공장 내 모든 부서에 최적의 모델을 배급함. (모든 함수명 지원)
# =========================================================

# 1. 환경 설정
FIXED_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=FIXED_ROOT / ".env")

API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_KEY_ANALYSIS")

if not API_KEY:
    # 키가 없어도 import는 되게 하되, 실행 시 에러 처리
    pass
else:
    genai.configure(api_key=API_KEY)

def find_best_model():
    """
    기본 모델 탐색 함수 (Strategy Judge 등에서 사용)
    """
    try:
        if not API_KEY: return 'models/gemini-1.5-pro-latest'

        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        candidates = []
        for m in all_models:
            name = m.lower()
            if 'gemini' not in name: continue
            if any(x in name for x in ['vision', 'nano', 'banana', 'robotics']): continue
            candidates.append(m)

        if not candidates:
            return 'models/gemini-1.5-pro-latest'

        # 점수 매기기
        scored_models = []
        for m in candidates:
            score = 0
            name = m.lower()
            if 'gemini-3' in name: score += 5000
            elif 'gemini-2.5' in name: score += 4000
            elif 'gemini-2.0' in name: score += 3000
            elif 'gemini-1.5' in name: score += 1000
            
            if 'deep-research' in name: score += 600
            elif 'pro' in name: score += 400
            elif 'flash' in name: score += 200
            
            if 'exp' in name or 'preview' in name: score += 50
            
            scored_models.append((score, m))

        scored_models.sort(key=lambda x: x[0], reverse=True)
        return scored_models[0][1]

    except Exception as e:
        print(f"⚠️ [Selector] 모델 탐색 실패: {e}")
        return 'models/gemini-1.5-pro-latest'

# 🔥 [호환성 패치] 다른 파일들이 'analyze_and_select_model'을 찾아도 작동하게 함
def analyze_and_select_model(role=None):
    """
    Creative Planner, Master Analyst 등에서 호출하는 함수
    role 인자가 들어와도 무시하고 최강 모델을 반환함.
    """
    return find_best_model()

if __name__ == "__main__":
    print(f"👑 [Selected Best Model]: {find_best_model()}")