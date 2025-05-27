import os

STATIC_BASE_URL = "/static"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")


def avatar_url(filename: str | None) -> str:
    if filename and os.path.exists(os.path.join(STATIC_DIR, "avatars", filename)):
        return f"{STATIC_BASE_URL}/avatars/{filename}"
    return f"{STATIC_BASE_URL}/default-avatar.svg"


def avatar_path(filename: str) -> str:
    return os.path.join(STATIC_DIR, "avatars", filename)


def banner_url(filename: str | None) -> str:
    if filename and os.path.exists(os.path.join(STATIC_DIR, "banners", filename)):
        return f"{STATIC_BASE_URL}/banners/{filename}"
    return f"{STATIC_BASE_URL}/default-banner.svg"


def banner_path(filename: str) -> str:
    return os.path.join(STATIC_DIR, "banners", filename)


def project_image_url(filename: str | None) -> str:
    if filename and os.path.exists(os.path.join(STATIC_DIR, "projects", filename)):
        return f"{STATIC_BASE_URL}/projects/{filename}"
    return f"{STATIC_BASE_URL}/default-banner.svg"


def project_image_path(filename: str) -> str:
    return os.path.join(STATIC_DIR, "projects", filename)


def partner_logo_url(filename: str | None) -> str:
    if filename and os.path.exists(os.path.join(STATIC_DIR, "partners", filename)):
        return f"{STATIC_BASE_URL}/partners/{filename}"
    return f"{STATIC_BASE_URL}/default-banner.svg"


def partner_logo_path(filename: str) -> str:
    return os.path.join(STATIC_DIR, "partners", filename)
