from constants import SOURCE_STATUS_MAP


def normalize_status(raw: str) -> str:
    key = (raw or "").strip().lower()
    for fragment, mapped in SOURCE_STATUS_MAP.items():
        if fragment in key:
            return mapped
    return "limited"