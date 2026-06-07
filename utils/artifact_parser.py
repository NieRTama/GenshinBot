import re


def extract_stats(text: str) -> dict:
    stats = {
        "crit_rate": 0.0,
        "crit_dmg": 0.0,
        "atk_pct": 0.0,
        "def_pct": 0.0,
        "energy_recharge": 0.0,
        "elemental_mastery": 0.0,
    }

    patterns = {
        "crit_rate": r"会心率\+([0-9]+(?:\.[0-9]+)?)%",
        "crit_dmg": r"会心ダメージ\+([0-9]+(?:\.[0-9]+)?)%",
        "atk_pct": r"攻撃力\+([0-9]+(?:\.[0-9]+)?)%",
        "def_pct": r"防御力\+([0-9]+(?:\.[0-9]+)?)%",
        "energy_recharge": r"元素チャージ効率\+([0-9]+(?:\.[0-9]+)?)%",
        "elemental_mastery": r"元素熟知\+([0-9]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            stats[key] = float(match.group(1))

    return stats
