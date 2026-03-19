"""Scraper registry."""

from .apple import AppleScraper
from .ashby import AshbyScraper
from .greenhouse import GreenhouseScraper
from .uber import UberScraper

SCRAPERS: dict[str, type] = {
    "greenhouse": GreenhouseScraper,
    "apple": AppleScraper,
    "ashby": AshbyScraper,
    "uber": UberScraper,
}


def get_scraper(scraper_type: str):
    cls = SCRAPERS.get(scraper_type)
    if not cls:
        raise ValueError(f"Unknown scraper type: {scraper_type}")
    return cls()
