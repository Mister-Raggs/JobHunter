"""Scraper registry."""

from .apple import AppleScraper
from .ashby import AshbyScraper
from .eightfold import EightfoldScraper
from .greenhouse import GreenhouseScraper
from .phenom import PhenomScraper
from .salesforce import SalesforceScraper
from .uber import UberScraper

SCRAPERS: dict[str, type] = {
    "greenhouse": GreenhouseScraper,
    "apple": AppleScraper,
    "ashby": AshbyScraper,
    "eightfold": EightfoldScraper,
    "phenom": PhenomScraper,
    "salesforce": SalesforceScraper,
    "uber": UberScraper,
}


def get_scraper(scraper_type: str):
    cls = SCRAPERS.get(scraper_type)
    if not cls:
        raise ValueError(f"Unknown scraper type: {scraper_type}")
    return cls()
