import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import click

from parsers.serp_parser import SerpParser
from parsers.response_validator import validate_input, ValidationError
from utils.request_manager import RequestManager
from utils.pagination_helper import Pagination

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "settings.json"
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_INPUT_FILE = DEFAULT_DATA_DIR / "input_keywords.txt"
DEFAULT_OUTPUT_FILE = DEFAULT_DATA_DIR / "example_output.json"

def load_settings(config_path: Path) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_data_dir(path: Path) -> None:
    os.makedirs(path.parent, exist_ok=True)

def search_once(
    client: RequestManager,
    parser: SerpParser,
    query: str,
    *,
    gl: Optional[str],
    hl: Optional[str],
    tbs: Optional[str],
    start: int,
    limit: int,
) -> Dict[str, Any]:
    url, params = client.build_query(
        query=query, gl=gl, hl=hl, tbs=tbs, start=start, num=min(limit, 100)
    )
    html = client.get(url, params=params)
    results = parser.parse(html)
    # Trim to desired limit for this page request
    results = results[: min(limit, len(results))]
    next_page, next_start = Pagination.next_page(start=start, page_size=params["num"], fetched=len(results))
    return {
        "query": query,
        "results": results,
        "next_page": next_page,
        "next_start": next_start,
    }

def run_for_query(
    client: RequestManager,
    parser: SerpParser,
    query: str,
    *,
    gl: Optional[str],
    hl: Optional[str],
    tbs: Optional[str],
    start: int,
    limit: int,
    pages: int,
) -> Dict[str, Any]:
    aggregated: List[Dict[str, Any]] = []
    current_start = start
    remaining = limit
    page_count = 0
    last_page_size = None

    while remaining > 0 and page_count < pages:
        page = search_once(
            client,
            parser,
            query,
            gl=gl,
            hl=hl,
            tbs=tbs,
            start=current_start,
            limit=min(remaining, 100),
        )
        page_results = page["results"]
        if not page_results:
            break

        # Adjust positions relative to absolute list
        absolute_offset = limit - remaining
        for idx, r in enumerate(page_results, start=1):
            r["position"] = absolute_offset + idx

        aggregated.extend(page_results)
        remaining -= len(page_results)
        current_start = page["next_start"] if page["next_start"] is not None else current_start + len(page_results)
        page_count += 1
        last_page_size = len(page_results)

        # If Google didn't return a full page, it's likely the end
        if last_page_size is not None and last_page_size < min(100, len(page_results)):
            break

        if page["next_start"] is None:
            break

    next_page, next_start = Pagination.next_page(start=current_start, page_size=10, fetched=0)
    return {
        "query": query,
        "results": aggregated[:limit],
        "next_page": next_page,
        "next_start": next_start,
    }

@click.command()
@click.option("--config", "config_path", type=click.Path(exists=True), default=str(DEFAULT_CONFIG_PATH), show_default=True, help="Path to settings.json")
@click.option("--input", "input_file", type=click.Path(exists=True), default=str(DEFAULT_INPUT_FILE), show_default=True, help="Path to input keywords file (one per line)")
@click.option("--output", "output_file", type=click.Path(), default=str(DEFAULT_OUTPUT_FILE), show_default=True, help="Path to write JSON results")
@click.option("--gl", type=str, default=None, help="Country code for results (e.g., US)")
@click.option("--hl", type=str, default=None, help="Interface language (e.g., en)")
@click.option("--tbs", type=str, default=None, help="Time-based filter string accepted by Google (e.g., qdr:d)")
@click.option("--start", type=int, default=0, show_default=True, help="Start index for results (pagination)")
@click.option("--limit", type=int, default=20, show_default=True, help="Max results per query (<= 1000 recommended)")
@click.option("--pages", type=int, default=2, show_default=True, help="Max number of pages to fetch per query")
def main(
    config_path: str,
    input_file: str,
    output_file: str,
    gl: Optional[str],
    hl: Optional[str],
    tbs: Optional[str],
    start: int,
    limit: int,
    pages: int,
) -> None:
    """
    CLI entrypoint to fetch Google SERP results for a list of keywords and save structured JSON.
    """
    try:
        settings = load_settings(Path(config_path))
        validate_input(start=start, limit=limit, pages=pages)
    except (json.JSONDecodeError, ValidationError) as e:
        raise SystemExit(f"[config/validation error] {e}")

    # Instantiate helpers
    client = RequestManager(
        base_url=settings.get("base_url", "https://www.google.com/search"),
        timeout=settings.get("timeout_seconds", 15),
        retries=settings.get("retries", 2),
        backoff=settings.get("retry_backoff_seconds", 1.0),
        default_params=settings.get("default_params", {}),
        default_headers=settings.get("default_headers", {}),
    )
    parser = SerpParser()

    # Read keywords
    with open(input_file, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]

    all_outputs: List[Dict[str, Any]] = []

    for q in keywords:
        try:
            result = run_for_query(
                client=client,
                parser=parser,
                query=q,
                gl=gl,
                hl=hl,
                tbs=tbs,
                start=start,
                limit=limit,
                pages=pages,
            )
            all_outputs.append(result)
        except Exception as e:
            all_outputs.append(
                {
                    "query": q,
                    "error": str(e),
                    "results": [],
                    "next_page": None,
                    "next_start": None,
                }
            )

    ensure_data_dir(Path(output_file))
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_outputs, f, ensure_ascii=False, indent=2)

    click.echo(f"Wrote {len(all_outputs)} query result blocks to {output_file}")

if __name__ == "__main__":
    main()