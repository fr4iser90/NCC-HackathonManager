def clean_dict(d: dict) -> dict:
    """Remove keys with None or empty string values from a dictionary."""
    return {k: v for k, v in d.items() if v not in (None, "")} 