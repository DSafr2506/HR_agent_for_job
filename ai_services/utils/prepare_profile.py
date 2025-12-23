from typing import Dict

def get_text_profile(user_profile: Dict) -> str:
    lines = []
    for key, value in user_profile.items():
        lines.append(f"{key}: {value}")
    text_profile = "\n".join(lines)
    return text_profile