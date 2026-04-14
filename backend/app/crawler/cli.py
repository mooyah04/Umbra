"""CLI entry point for the Umbra crawler.

Usage:
    python -m app.crawler.cli --seed "Elonmunk/tarren-mill/eu" --max-players 20 --depth 1
    python -m app.crawler.cli --seed "Elonmunk/tarren-mill/eu,Mooyuh/tarren-mill/eu" --max-players 1000 --depth 2 --region EU
"""

import argparse
import logging
import sys

from app.crawler.worker import crawl
from app.validators import ValidationError, validate_player_identity


def parse_seed(seed_str: str) -> list[dict]:
    """Parse seed string into validated, canonicalized player dicts.

    Format: "Name/realm-slug/region" or comma-separated for multiple.
    Example: "Elonmunk/tarren-mill/eu,Mooyuh/tarren-mill/eu"
    """
    players = []
    for entry in seed_str.split(","):
        parts = entry.strip().split("/")
        if len(parts) != 3:
            print(f"Invalid seed format: '{entry}' — expected 'Name/realm-slug/region'")
            sys.exit(1)
        try:
            name, realm, region = validate_player_identity(parts[0], parts[1], parts[2])
        except ValidationError as e:
            print(f"Invalid seed '{entry}': {e}")
            sys.exit(1)
        players.append({"name": name, "realm": realm, "region": region})
    return players


def main():
    parser = argparse.ArgumentParser(description="Umbra M+ Player Crawler")
    parser.add_argument(
        "--seed", required=True,
        help="Seed player(s): Name/realm-slug/region (comma-separated for multiple)",
    )
    parser.add_argument(
        "--max-players", type=int, default=100,
        help="Maximum number of players to ingest (default: 100)",
    )
    parser.add_argument(
        "--depth", type=int, default=2,
        help="BFS depth: 1 = seed's groupmates, 2 = groupmates of groupmates (default: 2)",
    )
    parser.add_argument(
        "--region", type=str, default=None,
        help="Only crawl players from this region (e.g., EU, US)",
    )
    parser.add_argument(
        "--rate", type=float, default=2.0,
        help="WCL API calls per second (default: 2.0)",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S",
    )

    seed_players = parse_seed(args.seed)

    print(f"Umbra Crawler")
    print(f"  Seeds: {len(seed_players)} player(s)")
    print(f"  Max players: {args.max_players}")
    print(f"  BFS depth: {args.depth}")
    print(f"  Region filter: {args.region or 'all'}")
    print(f"  Rate limit: {args.rate} calls/sec")
    print()

    result = crawl(
        seed_players=seed_players,
        max_players=args.max_players,
        max_depth=args.depth,
        region_filter=args.region,
        calls_per_second=args.rate,
    )

    print()
    print(f"Results:")
    print(f"  Ingested: {result['ingested']} "
          f"(seeds: {result.get('seed_ingested', 0)}, "
          f"groupmates: {result['ingested'] - result.get('seed_ingested', 0)})")
    print(f"  Failed: {result['failed']} (of which seeds: {result.get('seed_failed', 0)})")
    if result.get("seed_region_skipped", 0):
        print(f"  Seeds skipped by region filter: {result['seed_region_skipped']}")
    print(f"  Total seen: {result['seen']}")
    print(f"  Queue remaining: {result['queue_remaining']}")
    print(f"  Time: {result['elapsed_seconds']:.1f}s")

    # Non-zero exit if no seeds succeeded — surfaces cleanly to cron/CI.
    if result.get("seed_ingested", 0) == 0 and result.get("seed_failed", 0) > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
