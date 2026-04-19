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
    "zilliz": CompanyConfig(name="Zilliz", scraper="lever", slug="zilliz"),
    "mistral": CompanyConfig(name="Mistral AI", scraper="lever", slug="mistral"),
    "huggingface": CompanyConfig(name="Hugging Face", scraper="workable", slug="huggingface"),
    "writer": CompanyConfig(name="Writer", scraper="ashby", slug="writer"),
    "perplexity": CompanyConfig(name="Perplexity", scraper="ashby", slug="perplexity"),
    "cohere": CompanyConfig(name="Cohere", scraper="ashby", slug="cohere"),
    "goodfire": CompanyConfig(name="Goodfire", scraper="greenhouse", slug="goodfire"),
    "snorkelai": CompanyConfig(name="Snorkel AI", scraper="greenhouse", slug="snorkelai"),
    "lightningai": CompanyConfig(name="Lightning AI", scraper="greenhouse", slug="lightningai"),
    "chroma": CompanyConfig(name="Chroma", scraper="ashby", slug="trychroma"),
    "togetherai": CompanyConfig(name="Together AI", scraper="greenhouse", slug="togetherai"),
    "lambda": CompanyConfig(name="Lambda", scraper="ashby", slug="lambda"),
    "modal": CompanyConfig(name="Modal", scraper="ashby", slug="modal"),
    "crusoe": CompanyConfig(name="Crusoe Energy", scraper="ashby", slug="crusoe"),
    "nebius": CompanyConfig(name="Nebius", scraper="greenhouse", slug="nebius"),
    "cloudflare": CompanyConfig(name="Cloudflare", scraper="greenhouse", slug="cloudflare"),
    "clickhouse": CompanyConfig(name="ClickHouse", scraper="greenhouse", slug="clickhouse"),
    "dbtlabs": CompanyConfig(name="dbt Labs", scraper="greenhouse", slug="dbtlabsinc"),
    "pinterest": CompanyConfig(name="Pinterest", scraper="greenhouse", slug="pinterest"),
}
