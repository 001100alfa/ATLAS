"""005 — GBrain FTS entegrasyon testleri (AC1–AC6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.memory.gbrain import GBrain


def _brain(tmp_path: Path) -> GBrain:
    return GBrain(tmp_path / "vault", index_path=tmp_path / "idx.sqlite")


def test_recall_fts_happy(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("nota", "kesit hesabı için formüller", tags=("hesap",))
    b.remember("notb", "başka bir konu")
    hits = b.recall("kesit")
    assert hits
    assert hits[0].name == "nota"
    assert hits[0].score > 0


def test_recall_stale_otomatik_reindex(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("a", "eski içerik")
    b.index.ensure_fresh()
    # Vault'a düz dosya ekle — remember() değil, index bilmez
    (tmp_path / "vault" / "b.md").write_text("yeni haberler burada", encoding="utf-8")
    hits = b.recall("haberler")
    assert hits
    assert hits[0].name == "b"


def test_recall_silinen_not_donmez(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("silinecek", "gecici bilgi burada")
    b.recall("gecici")  # indeksi tazele
    (tmp_path / "vault" / "entities" / "silinecek.md").unlink()
    hits = b.recall("gecici")
    assert not any(h.name == "silinecek" for h in hits)


def test_recall_graf_komsusu(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("konsept", "kesit alanı formulu", links=("EN1993",))
    b.remember("EN1993", "yapı çeliği standardı")
    hits = b.recall("kesit")
    names = [h.name for h in hits]
    assert "konsept" in names
    assert "EN1993" in names  # komşu skoruyla geldi


def test_recall_fallback_fts_yoksa(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("a", "kesit hesabı formulleri")
    monkeypatch.setattr(b.index, "is_fts_available", lambda: False)
    hits = b.recall("kesit")
    assert hits and hits[0].name == "a"


def test_recall_bos_query(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("a", "içerik")
    assert b.recall("") == []
    assert b.recall("!!") == []


def test_context_for_calisir(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    b.remember("kesit", "I-kesit formülleri", tags=("EN1993",))
    ctx = b.context_for("kesit")
    assert "[[kesit]]" in ctx
    assert "GBrain bağlamı" in ctx


def test_context_for_bos(tmp_path: Path) -> None:
    b = _brain(tmp_path)
    assert "kayıtlı bağlam yok" in b.context_for("hicyok")
