import os


def _normalize_to_str(value):
    """
    Converte value in una stringa sicura per lo scenario_id.
    - str        -> str
    - dict       -> valori concatenati
    - list/tuple -> elementi concatenati
    - None       -> ""
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return "-".join(str(v) for v in value.values() if v is not None)

    if isinstance(value, (list, tuple, set)):
        return "-".join(
            _normalize_to_str(v) for v in value if _normalize_to_str(v)
        )

    return str(value)


def generate_scenario_id(
    video_path: str,
    odd_category,
    odd_subcategory,
    weather_type,
    has_pedestrians: bool,
    version: int = 1
):
    video_base = os.path.splitext(os.path.basename(video_path))[0]

    # --- ODD part (safe) ---
    odd_cat_str = _normalize_to_str(odd_category)
    odd_sub_str = _normalize_to_str(odd_subcategory)

    odd_part = odd_cat_str if odd_cat_str else "unknown"
    if odd_sub_str and odd_sub_str != "none":
        odd_part += f"-{odd_sub_str}"

    # --- CONDITIONS part (safe) ---
    cond = []

    weather_str = _normalize_to_str(weather_type)
    if weather_str and weather_str != "clear":
        cond.append(weather_str)

    if has_pedestrians:
        cond.append("pedestrians")

    cond_part = "-".join(cond) if cond else "normal"

    return f"{video_base}__{odd_part}__{cond_part}__v{version}"

