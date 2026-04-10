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
    "nuro": CompanyConfig(
        name="Nuro",
        scraper="greenhouse",
        slug="nuro",
    ),
    "otterai": CompanyConfig(
        name="Otter.ai",
        scraper="greenhouse",
        slug="otterai",
    ),
    "cvshealth": CompanyConfig(
        name="CVS Health",
        scraper="phenom",
        slug="cvshealth",
    ),
    "coreweave": CompanyConfig(
        name="CoreWeave",
        scraper="greenhouse",
        slug="coreweave",
    ),
    "braintrust": CompanyConfig(
        name="Braintrust",
        scraper="ashby",
        slug="braintrust",
    ),
    "glean": CompanyConfig(
        name="Glean",
        scraper="greenhouse",
        slug="gleanwork",
    ),
    "salesforce": CompanyConfig(
        name="Salesforce",
        scraper="salesforce",
        slug="salesforce",
    ),
    "qualcomm": CompanyConfig(
        name="Qualcomm",
        scraper="qualcomm",
        slug="qualcomm",
    ),
    "anthropic": CompanyConfig(
        name="Anthropic",
        scraper="greenhouse",
        slug="anthropic",
    ),
    "xai": CompanyConfig(
        name="xAI",
        scraper="greenhouse",
        slug="xai",
    ),
    "databricks": CompanyConfig(
        name="Databricks",
        scraper="greenhouse",
        slug="databricks",
    ),
    "scaleai": CompanyConfig(
        name="Scale AI",
        scraper="greenhouse",
        slug="scaleai",
    ),
    "pinecone": CompanyConfig(
        name="Pinecone",
        scraper="ashby",
        slug="pinecone",
    ),
    "arizeai": CompanyConfig(
        name="Arize AI",
        scraper="greenhouse",
        slug="arizeai",
    ),
    "domino": CompanyConfig(
        name="Domino Data Lab",
        scraper="greenhouse",
        slug="dominodatalab",
    ),
    "weaviate": CompanyConfig(
        name="Weaviate",
        scraper="ashby",
        slug="weaviate",
    ),
    "singlestore": CompanyConfig(
        name="SingleStore",
        scraper="greenhouse",
        slug="singlestore",
    ),
    "zilliz": CompanyConfig(
        name="Zilliz",
        scraper="lever",
        slug="zilliz",
    ),
}
