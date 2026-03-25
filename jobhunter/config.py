"""Company configurations for JobHunter."""

from dataclasses import dataclass


@dataclass
class CompanyConfig:
    name: str       # Display name
    scraper: str    # Scraper type: "greenhouse", "apple"
    slug: str       # Board identifier / slug


COMPANIES: dict[str, CompanyConfig] = {
    "doordash": CompanyConfig(
        name="DoorDash",
        scraper="greenhouse",
        slug="doordashusa",
    ),
    "apple": CompanyConfig(
        name="Apple",
        scraper="apple",
        slug="apple",
    ),
    "uber": CompanyConfig(
        name="Uber",
        scraper="uber",
        slug="uber",
    ),
    "baseten": CompanyConfig(
        name="Baseten",
        scraper="ashby",
        slug="baseten",
    ),
    "netflix": CompanyConfig(
        name="Netflix",
        scraper="eightfold",
        slug="netflix",
    ),
}
