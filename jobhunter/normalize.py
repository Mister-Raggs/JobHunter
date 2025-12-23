from urllib.parse import urlparse


def normalize_text(s: str) -> str:
    return " ".join(s.strip().lower().split())


def normalize_title(title: str) -> str:
    return normalize_text(title)


def normalize_company(company: str) -> str:
    return normalize_text(company)


REMOTE_SYNS = {"remote", "remote - us", "remote - usa", "fully remote"}
HYBRID_SYNS = {"hybrid", "flexible", "part-remote"}
ONSITE_SYNS = {"onsite", "on-site", "on site"}


def normalize_location(location: str) -> str:
    loc = normalize_text(location)
    if loc in REMOTE_SYNS:
        return "remote"
    if loc in HYBRID_SYNS:
        return "hybrid"
    if loc in ONSITE_SYNS:
        return "onsite"
    return loc


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    # Drop query and fragment to avoid source-specific tracking
    return f"{parsed.scheme}://{parsed.netloc}{path}" if parsed.scheme and parsed.netloc else path


def compute_role_id(company: str, source: str | None, source_id: str | None, url: str | None) -> str:
    comp = normalize_company(company)
    if source and source_id:
        return f"{comp}|{normalize_text(source)}:{normalize_text(source_id)}"
    if url:
        return f"{comp}|{canonical_url(url)}"
    # Fallback: company + normalized title isn't perfect but works for MVP
    return comp
