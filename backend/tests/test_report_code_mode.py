"""Report-code ingest mode: bypass the WCL character() lookup when it's
matching the wrong entity and pull fights directly from caller-supplied
log codes.

These tests verify the entry-point contract (schema acceptance, required
fields). End-to-end ingest with mocked WCL fight data is covered
separately — here we just confirm the routing decisions.
"""
import pytest

from app.schemas import IngestPlayer, IngestRequest


def test_schema_accepts_report_codes():
    p = IngestPlayer(
        name="Bannedkekw", realm="Tarren Mill", region="EU",
        class_name="Druid",
        report_codes=["XYZ123abc", "ABC456def"],
    )
    assert p.report_codes == ["XYZ123abc", "ABC456def"]


def test_schema_report_codes_optional():
    """Existing callers without report_codes must continue working."""
    p = IngestPlayer(name="Elonmunk", realm="Tarren Mill", region="EU")
    assert p.report_codes is None


def test_request_canonicalizes_report_codes_through():
    req = IngestRequest(
        players=[
            {
                "name": "Bannedkekw",
                "realm": "Tarren Mill",
                "region": "EU",
                "class_name": "Druid",
                "report_codes": ["abc123"],
            }
        ]
    )
    assert req.players[0].report_codes == ["abc123"]
    # Still normalized name/realm/region.
    assert req.players[0].name == "Bannedkekw"
    assert req.players[0].region == "EU"


def test_report_code_mode_requires_class_hint(monkeypatch):
    """Without class_hint, report-code mode can't correctly label the
    player's class (since we're explicitly bypassing WCL's class match).
    Ingest should refuse rather than guess wrong."""
    from app.pipeline import ingest

    # Block any WCL call — we should never make one if class_hint is missing.
    monkeypatch.setattr(
        ingest.wcl_client, "get_character_with_reports",
        lambda **kw: (_ for _ in ()).throw(AssertionError("should not call WCL")),
    )
    monkeypatch.setattr(
        ingest.wcl_client, "get_report_fights",
        lambda code: (_ for _ in ()).throw(AssertionError("should not call WCL")),
    )

    class _FakeSession:
        def execute(self, *a, **kw): return self
        def scalar_one_or_none(self): return None
        def scalars(self): return []
        def add(self, *a, **kw): pass
        def flush(self): pass
        def delete(self, *a): pass
        def commit(self): pass

    result = ingest.ingest_player(
        _FakeSession(), "Bannedkekw", "Tarren Mill", "EU",
        class_hint=None,
        report_codes=["some-code"],
    )
    assert result.player is None
    assert result.reason == "class_hint_required"
