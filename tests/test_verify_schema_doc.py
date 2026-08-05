"""SPEC 061 — docs/api/vault-verify-schema.json JSON Schema doğrulama testleri.

Şema tanımı ile canlı `to_dict()` çıktısının uyumluluğunu garantile.
"""

from __future__ import annotations

import json
from pathlib import Path

from atlas_core.memory.vault import Vault
from atlas_core.memory.vault_verify import BrokenLink, VerifyReport, verify_graph

_REPO = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO / "docs" / "api" / "vault-verify-schema.json"


def _load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _make_vault(root: Path, notes: dict[str, str]) -> Vault:
    root.mkdir(parents=True, exist_ok=True)
    for name, content in notes.items():
        (root / f"{name}.md").write_text(content, encoding="utf-8")
    return Vault(root)


# ═════════════════════════════════════════════════════════════════════
# Şema dosyası bütünlüğü
# ═════════════════════════════════════════════════════════════════════


def test_061_schema_dosyasi_mevcut() -> None:
    assert _SCHEMA_PATH.is_file()


def test_061_schema_valid_json() -> None:
    data = _load_schema()
    assert isinstance(data, dict)


def test_061_schema_draft_07() -> None:
    schema = _load_schema()
    assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
    assert "$id" in schema
    assert "title" in schema


def test_061_schema_root_object() -> None:
    schema = _load_schema()
    assert schema.get("type") == "object"
    assert schema.get("additionalProperties") is False
    # Zorunlu alanlar to_dict() ile eşleşmeli
    required = set(schema.get("required", []))
    assert required == {
        "broken_links", "orphan_notes", "orphan_tags",
        "notes_total", "links_total", "tags_total", "is_clean",
    }


def test_061_schema_broken_links_yapisi() -> None:
    schema = _load_schema()
    bl = schema["properties"]["broken_links"]
    assert bl["type"] == "array"
    item = bl["items"]
    assert set(item["required"]) == {"from", "to"}
    assert item["additionalProperties"] is False


def test_061_schema_integer_alan_minimum_0() -> None:
    """Sayaçlar (notes/links/tags_total) 0'dan küçük olamaz."""
    schema = _load_schema()
    for field in ("notes_total", "links_total", "tags_total"):
        assert schema["properties"][field]["type"] == "integer"
        assert schema["properties"][field]["minimum"] == 0


# ═════════════════════════════════════════════════════════════════════
# Canlı to_dict() çıktısı şemaya uyumlu
# ═════════════════════════════════════════════════════════════════════


def _validate_against_schema(instance: dict, schema: dict) -> list[str]:
    """Minimal Draft-07 doğrulayıcı (dış bağımlılık yok).

    Şu kontrolleri yapar: required alanlar, additionalProperties, type,
    integer minimum, array items required + additionalProperties.
    """
    errors: list[str] = []
    # required
    for req in schema.get("required", []):
        if req not in instance:
            errors.append(f"eksik alan: {req}")
    # additionalProperties=false → yalnız property listesindekiler
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}).keys())
        for key in instance:
            if key not in allowed:
                errors.append(f"beklenmeyen alan: {key}")
    # per-property type/min
    for name, spec in schema.get("properties", {}).items():
        if name not in instance:
            continue
        value = instance[name]
        t = spec.get("type")
        if t == "integer" and not isinstance(value, int):
            errors.append(f"{name} integer olmalı, {type(value).__name__} geldi")
        elif t == "boolean" and not isinstance(value, bool):
            errors.append(f"{name} bool olmalı")
        elif t == "array" and not isinstance(value, list):
            errors.append(f"{name} array olmalı")
        elif t == "string" and not isinstance(value, str):
            errors.append(f"{name} string olmalı")
        elif t == "object" and not isinstance(value, dict):
            errors.append(f"{name} object olmalı")
        if t == "integer" and isinstance(value, int):
            minimum = spec.get("minimum")
            if minimum is not None and value < minimum:
                errors.append(f"{name} minimum {minimum}, {value} geldi")
        # array items
        if t == "array" and isinstance(value, list):
            item_spec = spec.get("items", {})
            item_required = item_spec.get("required", [])
            item_allowed = set(item_spec.get("properties", {}).keys())
            for i, item in enumerate(value):
                if item_spec.get("type") == "object" and not isinstance(item, dict):
                    errors.append(f"{name}[{i}] object olmalı")
                    continue
                if not isinstance(item, dict):
                    continue
                for req in item_required:
                    if req not in item:
                        errors.append(f"{name}[{i}] eksik alan: {req}")
                if item_spec.get("additionalProperties") is False:
                    for key in item:
                        if key not in item_allowed:
                            errors.append(f"{name}[{i}] beklenmeyen alan: {key}")
    return errors


def test_061_temiz_report_semaya_uyumlu(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"a": "[[b]]", "b": "[[a]]"})
    report = verify_graph(v.graph())
    schema = _load_schema()
    errors = _validate_against_schema(report.to_dict(), schema)
    assert errors == [], f"şema ihlali: {errors}"


def test_061_bulgu_report_semaya_uyumlu(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {
        "a": "[[yok]] #tek",
        "b": "[[a]] #ortak",
        "c": "[[a]] #ortak",
        "yalniz": "solo",
    })
    report = verify_graph(v.graph())
    schema = _load_schema()
    errors = _validate_against_schema(report.to_dict(), schema)
    assert errors == [], f"şema ihlali: {errors}"


def test_061_manuel_report_semaya_uyumlu() -> None:
    """Farklı senaryolar: broken_link farklı sayı, boş listeler."""
    report = VerifyReport(
        broken_links=[BrokenLink(frm="a", to="x")],
        orphan_notes=["yalniz"],
        orphan_tags=["stub"],
        notes_total=5,
        links_total=3,
        tags_total=2,
    )
    schema = _load_schema()
    errors = _validate_against_schema(report.to_dict(), schema)
    assert errors == []


def test_061_sema_ekstra_alan_reddeder() -> None:
    """Şema `additionalProperties: false` → ekstra alan tespit edilir."""
    schema = _load_schema()
    instance = {
        "broken_links": [], "orphan_notes": [], "orphan_tags": [],
        "notes_total": 0, "links_total": 0, "tags_total": 0,
        "is_clean": True,
        "extra_field": "kabul edilmemeli",
    }
    errors = _validate_against_schema(instance, schema)
    assert any("beklenmeyen alan: extra_field" in e for e in errors)


def test_061_sema_eksik_zorunlu_reddeder() -> None:
    schema = _load_schema()
    instance = {"broken_links": []}  # 6 zorunlu eksik
    errors = _validate_against_schema(instance, schema)
    assert len([e for e in errors if e.startswith("eksik alan")]) == 6


def test_061_sema_yanlis_tip_reddeder() -> None:
    schema = _load_schema()
    instance = {
        "broken_links": [], "orphan_notes": [], "orphan_tags": [],
        "notes_total": "beş",  # int değil
        "links_total": 0, "tags_total": 0, "is_clean": True,
    }
    errors = _validate_against_schema(instance, schema)
    assert any("notes_total integer olmalı" in e for e in errors)
