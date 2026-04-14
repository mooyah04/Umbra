"""Crawler diagnostics — verify failure signalling and region-filter logging."""
import logging
from unittest.mock import patch

import pytest

from app.crawler import worker as crawler_worker
from app.pipeline.ingest import IngestResult


@pytest.fixture
def no_sleep(monkeypatch):
    """Strip rate-limiter waits so tests run instantly."""
    monkeypatch.setattr(crawler_worker.RateLimiter, "wait", lambda self: None)


@pytest.fixture
def null_session(monkeypatch):
    """Don't require a real DB — mock SessionLocal to a dummy context."""
    class _FakeSession:
        def close(self): pass
    monkeypatch.setattr(crawler_worker, "SessionLocal", lambda: _FakeSession())


def test_region_filter_excludes_seed_with_warning(no_sleep, null_session, caplog):
    """A seed whose region doesn't match --region should produce a visible warning,
    not silently vanish."""
    seeds = [{"name": "Alice", "realm": "TarrenMill", "region": "EU"}]
    with patch("app.crawler.worker.ingest_player") as mock_ingest, caplog.at_level(logging.WARNING):
        result = crawler_worker.crawl(
            seed_players=seeds, max_players=10, max_depth=1,
            region_filter="US", calls_per_second=1000,
        )
    mock_ingest.assert_not_called()
    assert result["seed_region_skipped"] == 1
    assert result["ingested"] == 0
    assert any("skipped" in r.message.lower() and "region" in r.message.lower()
               for r in caplog.records)


def test_crawl_with_no_valid_seeds_exits_early(no_sleep, null_session, caplog):
    seeds = [{"name": "Alice", "realm": "TM", "region": "EU"}]
    with patch("app.crawler.worker.ingest_player") as mock_ingest, caplog.at_level(logging.ERROR):
        result = crawler_worker.crawl(
            seed_players=seeds, max_players=10, max_depth=1,
            region_filter="US",  # excludes the only seed
            calls_per_second=1000,
        )
    mock_ingest.assert_not_called()
    assert result["ingested"] == 0
    assert any("cannot start" in r.message.lower() for r in caplog.records)


def test_all_seeds_failing_logs_all_seeds_failed(no_sleep, null_session, caplog):
    """When every seed fails to ingest, crawler must log an ERROR surfacing this
    as the likely root cause (bad creds, wrong realm slugs, etc.)."""
    seeds = [
        {"name": "A", "realm": "X", "region": "US"},
        {"name": "B", "realm": "Y", "region": "US"},
    ]
    with patch(
        "app.crawler.worker.ingest_player",
        return_value=IngestResult(player=None, reason="wcl_not_found"),
    ), caplog.at_level(logging.ERROR):
        result = crawler_worker.crawl(
            seed_players=seeds, max_players=10, max_depth=1,
            calls_per_second=1000,
        )
    assert result["seed_ingested"] == 0
    assert result["seed_failed"] == 2
    assert any("ALL" in r.message and "SEEDS FAILED" in r.message for r in caplog.records)


def test_ingest_reason_surfaces_in_log(no_sleep, null_session, caplog):
    """The IngestResult.reason field should appear in per-failure log lines."""
    seeds = [{"name": "Ghostly", "realm": "Zul'jin", "region": "US"}]
    with patch(
        "app.crawler.worker.ingest_player",
        return_value=IngestResult(player=None, reason="wcl_not_found"),
    ), caplog.at_level(logging.WARNING):
        crawler_worker.crawl(
            seed_players=seeds, max_players=10, max_depth=1,
            calls_per_second=1000,
        )
    assert any("wcl_not_found" in r.message for r in caplog.records)


def test_seed_vs_groupmate_counters(no_sleep, null_session):
    """Distinct success counters for seeds vs discovered groupmates."""
    seeds = [{"name": "Seed", "realm": "R", "region": "US"}]

    class _FakePlayer:
        pass

    call_state = {"n": 0}

    def fake_ingest(session, name, realm, region):
        call_state["n"] += 1
        if call_state["n"] == 1:
            return IngestResult(
                player=_FakePlayer(),
                groupmates=[{"name": "GM", "realm": "R", "region": "US"}],
            )
        return IngestResult(player=_FakePlayer(), groupmates=[])

    with patch("app.crawler.worker.ingest_player", side_effect=fake_ingest):
        result = crawler_worker.crawl(
            seed_players=seeds, max_players=10, max_depth=1,
            calls_per_second=1000,
        )
    assert result["ingested"] == 2
    assert result["seed_ingested"] == 1
    assert result["seed_failed"] == 0
