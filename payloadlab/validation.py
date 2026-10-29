"""Input validation helpers."""


def optional_limit_status(value: float, limit: float | None) -> tuple[str, float | None]:
    if limit is None or limit <= 0:
        return "NOT SET", None
    margin = limit - value
    return ("PASS" if margin >= 0 else "FAIL"), margin


def envelope_status(dimensions_mm, envelope_mm) -> tuple[str, list[float] | None]:
    if envelope_mm is None or any(v <= 0 for v in envelope_mm):
        return "NOT SET", None
    margins = [e - d for d, e in zip(dimensions_mm, envelope_mm)]
    return ("PASS" if min(margins) >= 0 else "FAIL"), margins
