import yaml
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROMPT_DIR = CURRENT_DIR / "prompts"

def load_prompt(filename, **kwargs):
    try:
        file_path = PROMPT_DIR / filename
        if not file_path.exists(): return f"Error: {filename} not found", ""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        sys_p = data.get('system', '')
        usr_p = data.get('user', '')
        if kwargs:
            try:
                sys_p = sys_p.format(**kwargs)
                usr_p = usr_p.format(**kwargs)
            except: pass
        return sys_p, usr_p
    except: return "", ""
