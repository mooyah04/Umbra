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
    start_time = time.time()

    # Seed the queue
    for p in seed_players:
        key = f"{p['name']}-{p['realm']}".lower()
        if key not in seen:
            seen.add(key)
            queue.append((p, 0))

    logger.info(
        "Starting crawl: %d seeds, max %d players, depth %d",
        len(seed_players), max_players, max_depth,
    )

    while queue and ingested_count < max_players:
        player_dict, depth = queue.popleft()
        name = player_dict["name"]
        realm = player_dict["realm"]
        region = player_dict["region"]

        # Apply region filter
        if region_filter and region.upper() != region_filter.upper():
            continue

        # Progress logging
        elapsed = time.time() - start_time
        rate = ingested_count / elapsed if elapsed > 0 else 0
        remaining = (max_players - ingested_count) / rate if rate > 0 else 0
        logger.info(
            "[%d/%d] Ingesting %s-%s (depth %d, queue: %d, %.1f players/min, ~%.0f min remaining)",
            ingested_count + 1, max_players, name, realm,
            depth, len(queue), rate * 60, remaining / 60,
        )

        # Rate limit and ingest
        limiter.wait()

        session = SessionLocal()
        try:
            result = ingest_player(session, name, realm, region)

            if result.player:
                ingested_count += 1

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
            else:
                failed_count += 1
                logger.warning("  Failed to ingest %s-%s", name, realm)

        except WCLQueryError as e:
            failed_count += 1
            logger.error("  WCL error for %s-%s: %s", name, realm, e)
        except Exception as e:
            failed_count += 1
            logger.error("  Unexpected error for %s-%s: %s", name, realm, e)
        finally:
            session.close()

    elapsed = time.time() - start_time
    logger.info(
        "Crawl complete: %d ingested, %d failed, %d seen, %.1f minutes",
        ingested_count, failed_count, len(seen), elapsed / 60,
    )

    return {
        "ingested": ingested_count,
        "failed": failed_count,
        "seen": len(seen),
        "queue_remaining": len(queue),
        "elapsed_seconds": round(elapsed, 1),
    }
