import argparse
import json
from pathlib import Path

from . import __version__
from .normalize import (
    normalize_title,
    normalize_company,
    normalize_location,
    canonical_url,
    compute_role_id,
)
from .storage import load_store, save_store, update_role


def cmd_ingest(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    store_path = Path(args.store)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        posting = json.load(f)

    company = posting.get("company", "")
    title = posting.get("title", "")
    location = posting.get("location", "")
    source = posting.get("source")
    source_id = posting.get("source_id")
    url = posting.get("url")

    normalized = {
        "company": normalize_company(company),
        "title": normalize_title(title),
        "location": normalize_location(location),
        "url": canonical_url(url) if url else None,
        "source": source,
        "source_id": source_id,
    }

    role_id = compute_role_id(company, source, source_id, url)
    store = load_store(store_path)
    result = update_role(store, role_id, normalized)
    save_store(store_path, store)

    status = result["status"]
    print(f"Role: {role_id}")
    print(f"Status: {status}")
    if result["changes"]:
        print("Changes:")
        for k, v in result["changes"].items():
            print(f" - {k}: {v['old']} -> {v['new']}")


def main():
    parser = argparse.ArgumentParser(prog="jobhunter", description="Job Hunter — clean MVP CLI")
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command")
    ing = subparsers.add_parser("ingest", help="Ingest a single posting JSON and persist state")
    ing.add_argument("--input", required=True, help="Path to posting JSON input")
    ing.add_argument("--store", default="data/store.json", help="Path to JSON store (default: data/store.json)")
    ing.set_defaults(func=cmd_ingest)

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if hasattr(args, "func"):
        args.func(args)
        return

    print("Job Hunter reset: ready to build MVP.")


if __name__ == "__main__":
    main()
