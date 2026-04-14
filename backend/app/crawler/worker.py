"""BFS crawler that discovers and ingests players by following groupmate connections."""

import logging
import time
from collections import deque

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawler.rate_limiter import RateLimiter
from app.db import SessionLocal
from app.models import Player
from app.pipeline.ingest import ingest_player, IngestResult
from app.wcl.client import WCLQueryError

logger = logging.getLogger(__name__)


def _player_exists(session: Session, name: str, realm: str) -> bool:
    """Check if a player is already in the database."""
    stmt = select(Player).where(
        Player.name.ilike(name),
        Player.realm.ilike(realm),
    )
    return session.execute(stmt).scalar_one_or_none() is not None


def crawl(
    seed_players: list[dict],
    max_players: int = 100,
    max_depth: int = 2,
    region_filter: str | None = None,
    calls_per_second: float = 2.0,
):
    """Crawl WCL for players using BFS groupmate discovery.

    Args:
        seed_players: Starting players [{name, realm, region}, ...]
        max_players: Maximum number of players to ingest.
        max_depth: BFS depth (1 = seed's groupmates, 2 = groupmates of groupmates).
        region_filter: Only crawl players from this region (e.g., "EU").
        calls_per_second: Rate limit for WCL API calls.
    """
    limiter = RateLimiter(calls_per_second)

    # BFS queue: (player_dict, depth)
    queue: deque[tuple[dict, int]] = deque()
    seen: set[str] = set()
    ingested_count = 0
    failed_count = 0
    seed_ingested = 0
    seed_failed = 0
    seed_region_skipped = 0
    start_time = time.time()

    # Validate + seed the queue. Log when a seed is skipped by the region filter
    # so "0 ingested" isn't mysterious.
    seed_count = 0
    for p in seed_players:
        if region_filter and p["region"].upper() != region_filter.upper():
            seed_region_skipped += 1
            logger.warning(
                "Seed %s-%s skipped: region %s excluded by --region %s filter",
                p["name"], p["realm"], p["region"], region_filter,
            )
            continue
        key = f"{p['name']}-{p['realm']}".lower()
        if key not in seen:
            seen.add(key)
            queue.append((p, 0))
            seed_count += 1

    logger.info(
        "Starting crawl: %d seeds queued (%d skipped by region filter), max %d players, depth %d",
        seed_count, seed_region_skipped, max_players, max_depth,
    )

    if seed_count == 0:
        logger.error(
            "No seeds survived validation — crawl cannot start. "
            "Check --region filter and seed formatting."
        )
        return {
            "ingested": 0, "failed": 0, "seen": 0,
            "queue_remaining": 0, "elapsed_seconds": 0.0,
            "seed_ingested": 0, "seed_failed": 0,
            "seed_region_skipped": seed_region_skipped,
        }

    while queue and ingested_count < max_players:
        player_dict, depth = queue.popleft()
        name = player_dict["name"]
        realm = player_dict["realm"]
        region = player_dict["region"]
        is_seed = depth == 0

        # Region filter for discovered groupmates (seeds were filtered above).
        if region_filter and region.upper() != region_filter.upper():
            continue

        # Progress logging
        elapsed = time.time() - start_time
        rate = ingested_count / elapsed if elapsed > 0 else 0
        remaining = (max_players - ingested_count) / rate if rate > 0 else 0
        logger.info(
            "[%d/%d] Ingesting %s%s-%s (depth %d, queue: %d, %.1f players/min, ~%.0f min remaining)",
            ingested_count + 1, max_players,
            "[SEED] " if is_seed else "", name, realm,
            depth, len(queue), rate * 60, remaining / 60,
        )

        # Rate limit and ingest
        limiter.wait()

        session = SessionLocal()
        try:
            result = ingest_player(session, name, realm, region)

            if result.player:
                ingested_count += 1
                if is_seed:
                    seed_ingested += 1

                # Queue groupmates if within depth limit
                if depth < max_depth:
                    new_groupmates = 0
                    for gm in result.groupmates:
                        gm_key = f"{gm['name']}-{gm['realm']}".lower()
                        if gm_key not in seen:
                            seen.add(gm_key)
                            queue.append((gm, depth + 1))
                            new_groupmates += 1

                    if new_groupmates > 0:
                        logger.info(
                            "  Discovered %d new groupmates (queue now: %d)",
                            new_groupmates, len(queue),
                        )
                elif is_seed:
                    logger.info("  Seed ingested but depth=0 — no groupmate expansion.")
            else:
                failed_count += 1
                if is_seed:
                    seed_failed += 1
                level = logger.error if is_seed else logger.warning
                reason = result.reason or "unknown"
                level(
                    "  %s%s-%s ingest failed: %s",
                    "[SEED] " if is_seed else "", name, realm, reason,
                )

        except WCLQueryError as e:
            failed_count += 1
            if is_seed:
                seed_failed += 1
            logger.error(
                "  %s%s-%s WCL error: %s",
                "[SEED] " if is_seed else "", name, realm, e,
            )
        except Exception as e:
            failed_count += 1
            if is_seed:
                seed_failed += 1
            logger.error(
                "  %s%s-%s unexpected error: %s",
                "[SEED] " if is_seed else "", name, realm, e,
                exc_info=True,
            )
        finally:
            session.close()

    elapsed = time.time() - start_time
    logger.info(
        "Crawl complete: %d ingested (%d seeds / %d groupmates), %d failed, %d seen, %.1f minutes",
        ingested_count, seed_ingested, ingested_count - seed_ingested,
        failed_count, len(seen), elapsed / 60,
    )

    # Loud warning if every seed failed — the crawl discovered nothing.
    if seed_count > 0 and seed_ingested == 0:
        logger.error(
            "ALL %d SEEDS FAILED. No groupmates were discovered. "
            "Check WCL credentials, seed formatting, and realm slugs.",
            seed_count,
        )

    return {
        "ingested": ingested_count,
        "failed": failed_count,
        "seen": len(seen),
        "queue_remaining": len(queue),
        "elapsed_seconds": round(elapsed, 1),
        "seed_ingested": seed_ingested,
        "seed_failed": seed_failed,
        "seed_region_skipped": seed_region_skipped,
    }
