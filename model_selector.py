import os
import google.generativeai as genai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# =========================================================
# 📅 2026.02 Latest Model Lineup (Authorized by CEO)
# =========================================================

MODEL_SPECS = {
    "GOOGLE": {
        "flagship": "models/gemini-3-pro",        # 복잡한 추론, 코딩, 데이터 분석 (Main)
        "fast": "models/gemini-3-flash",          # 대량 쿼리, 속도 최적화
        "reasoning": "models/gemini-3-deep-think",# 과학/공학 특수 추론
        "legacy": "models/gemini-2.5-pro"         # 안정성 백업용
    },
    "OPENAI": {
        "flagship": "gpt-5.2",           # 2025.12 출시 최신작 (Main)
        "fast": "gpt-5-nano",            # 초고속 경량 모델
        "reasoning": "o3",               # STEM/코딩 특화 (Thinking Process)
        "creative": "gpt-5.2"            # 창작에도 5.2가 우세
    },
    "ANTHROPIC": {
        "flagship": "claude-opus-4.6",   # 1M 컨텍스트, 기업용 에이전트 (Main)
        "balanced": "claude-3-7-sonnet", # 속도/성능 균형
        "fast": "claude-3-5-haiku"       # 실시간 응답
    }
}

def get_api_key(provider="GOOGLE"):
    """제공자별 API 키를 가져옵니다."""
    if provider == "GOOGLE":
        return os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
    elif provider == "OPENAI":
        return os.getenv("OPENAI_API_KEY")
    elif provider == "ANTHROPIC":
        return os.getenv("ANTHROPIC_API_KEY")
    return None

def find_best_model(task_type="creative"):
    """
    작업 유형(task_type)에 따라 2026년 최적의 모델을 반환합니다.
    
    Args:
        task_type (str): 'creative' (기획/창작), 'logic' (추론/분석), 'coding' (코딩), 'speed' (단순작업)
    
    Returns:
        str: 모델명 (예: 'models/gemini-3-pro')
    """
    # 우선순위: GOOGLE (기본) -> OPENAI -> ANTHROPIC
    # 사장님의 지갑 사정과 API 키 유무에 따라 자동 배차합니다.

    google_key = get_api_key("GOOGLE")
    openai_key = get_api_key("OPENAI")
    anthropic_key = get_api_key("ANTHROPIC")

    # 1. 창의적 기획 / 메인 집필 (Creative)
    if task_type == "creative":
        if google_key: return MODEL_SPECS["GOOGLE"]["flagship"] # Gemini 3 Pro
        if openai_key: return MODEL_SPECS["OPENAI"]["flagship"] # GPT-5.2
        if anthropic_key: return MODEL_SPECS["ANTHROPIC"]["flagship"] # Opus 4.6

    # 2. 논리적 분석 / 비평 / 전략 수립 (Logic & Reasoning)
    elif task_type == "logic":
        if openai_key: return MODEL_SPECS["OPENAI"]["reasoning"] # o3 (Thinking)
        if google_key: return MODEL_SPECS["GOOGLE"]["reasoning"] # Gemini 3 Deep Think
        if anthropic_key: return MODEL_SPECS["ANTHROPIC"]["flagship"] # Opus 4.6

    # 3. 코딩 / 시스템 구축 (Coding)
    elif task_type == "coding":
        if openai_key: return MODEL_SPECS["OPENAI"]["reasoning"] # o3 (Coding King)
        if google_key: return MODEL_SPECS["GOOGLE"]["flagship"] # Gemini 3 Pro
        
    # 4. 단순 요약 / 빠른 처리 (Speed)
    elif task_type == "speed":
        if google_key: return MODEL_SPECS["GOOGLE"]["fast"] # Gemini 3 Flash
        if openai_key: return MODEL_SPECS["OPENAI"]["fast"] # GPT-5-nano
        if anthropic_key: return MODEL_SPECS["ANTHROPIC"]["fast"] # Haiku

    # 기본값 (Fallback)
    return "models/gemini-3-pro"

# 테스트용
if __name__ == "__main__":
    print(f"🚀 [2026 Engine Check]")
    print(f" - Creative Engine: {find_best_model('creative')}")
    print(f" - Logic Engine:    {find_best_model('logic')}")
    print(f" - Speed Engine:    {find_best_model('speed')}")