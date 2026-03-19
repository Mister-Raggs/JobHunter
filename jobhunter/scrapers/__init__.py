"""Scraper registry."""

from .apple import AppleScraper
from .greenhouse import GreenhouseScraper

SCRAPERS: dict[str, type] = {
    "greenhouse": GreenhouseScraper,
    "apple": AppleScraper,
}


def get_scraper(scraper_type: str):
    cls = SCRAPERS.get(scraper_type)
    if not cls:
        raise ValueError(f"Unknown scraper type: {scraper_type}")
    return cls()
