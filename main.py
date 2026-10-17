"""Run the Alibaba Products Scraper on Apify and save its results as JSON and CSV.

Actor page: https://apify.com/DevilScrapes/alibaba-products-scraper
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

from apify_client import ApifyClient

ACTOR_ID = "DevilScrapes/alibaba-products-scraper"
TERMINAL_OK = "SUCCEEDED"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Alibaba Products Scraper on Apify.")
    parser.add_argument("input", nargs="?", default="input.json", help="Actor input JSON file (default: input.json)")
    parser.add_argument("--out", default=".", help="Folder for results.json and results.csv (default: here)")
    parser.add_argument("--max-charge", type=Decimal, help="Stop the run once it has cost this many USD")
    parser.add_argument("--memory", type=int, help="Run memory in MB (default: the Actor's own setting)")
    return parser.parse_args(argv)


def load_input(path: str) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Input file not found: {path}")
    except json.JSONDecodeError as error:
        sys.exit(f"Input file {path} is not valid JSON: {error}")
    if not isinstance(data, dict):
        sys.exit(f"Input file {path} must contain a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN first. Get a token at https://console.apify.com/settings/integrations")

    run_input = load_input(args.input)
    client = ApifyClient(token, api_url=os.environ.get("APIFY_API_URL", "https://api.apify.com"))

    print(f"Starting {ACTOR_ID} ...")
    run = client.actor(ACTOR_ID).call(
        run_input=run_input,
        max_total_charge_usd=args.max_charge,
        memory_mbytes=args.memory,
    )
    if run is None:
        sys.exit("The run could not be started.")

    print(f"Run {run.id} finished: {run.status}")
    print(f"Details: https://console.apify.com/actors/runs/{run.id}")
    if run.status != TERMINAL_OK:
        print(run.status_message or "No status message.", file=sys.stderr)
        return 1

    dataset = client.dataset(run.default_dataset_id)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    items = json.loads(dataset.get_items_as_bytes(item_format="json", clean=True))
    (out / "results.json").write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "results.csv").write_bytes(dataset.get_items_as_bytes(item_format="csv", clean=True))

    print(f"Saved {len(items)} items to {out / 'results.json'} and {out / 'results.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
