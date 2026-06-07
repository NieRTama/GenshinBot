def calculate_score(stats: dict, mode: str = "cr") -> float:
    crit = stats["crit_rate"] * 2 + stats["crit_dmg"]

    if mode == "cr":
        return crit
    if mode == "a":
        return crit + stats["atk_pct"] * 1.5
    if mode == "e":
        return crit + stats["elemental_mastery"] / 4
    if mode == "ch":
        return crit + stats["energy_recharge"] * 1.2
    if mode == "d":
        return crit + stats["def_pct"] * 1.5

    return crit
