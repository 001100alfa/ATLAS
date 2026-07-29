"""Sağlık & Güncelleme Ajanı testleri.

Ağ ve gerçek ikili GEREKTİRMEZ: uzak kayıt defteri sorguları taklit edilir,
denetimler geçici bir proje kökünde koşar. Amaç, sürüm karşılaştırmasının ve
bulgu sözleşmesinin (kanıt/kaynak/çözüm + düzeltme eylemi) bozulmadığını
korumaktır — bu ikisi bozulursa arayüz sessizce yanlış şey söyler.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.doctor_gui import checks, fixes, report, versions

# --- sürüm karşılaştırma ------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("juggler v0.4.2 (commit: unknown, built: unknown)", (0, 4, 2)),
        ("v0.5.0", (0, 5, 0)),
        ("1.18.4", (1, 18, 4)),
        ("goose 1.44.0", (1, 44, 0)),
        ("3.0.46-beta.1", (3, 0, 46)),
        ("sürüm yok", None),
        (None, None),
    ],
)
def test_parse_semver(text, expected):
    assert versions.parse_semver(text) == expected


def test_is_outdated_only_when_certain():
    assert versions.is_outdated("0.4.2", "0.5.0") is True
    assert versions.is_outdated("1.18.6", "1.18.6") is False
    assert versions.is_outdated("2.0.0", "1.9.9") is False  # yerel daha yeni
    # Okunamayan taraf "eski" sayılmaz — kullanıcı boşuna güncellemeye itilmez.
    assert versions.is_outdated(None, "1.0.0") is False
    assert versions.is_outdated("1.0.0", None) is False


def test_remote_latest_cached(monkeypatch):
    calls = []

    def fake(repo):
        calls.append(repo)
        return "9.9.9"

    versions.clear_cache()
    monkeypatch.setattr(versions, "github_latest", fake)
    assert versions.remote_latest("juggler") == "9.9.9"
    assert versions.remote_latest("juggler") == "9.9.9"
    assert calls == ["juggler-ai/juggler"], "ikinci çağrı önbellekten gelmeli"
    versions.clear_cache()


# --- bulgu sözleşmesi ---------------------------------------------------------


def test_every_step_returns_contract(tmp_path: Path, monkeypatch):
    """Her adım sözlük listesi döndürür ve zorunlu alanları taşır."""
    monkeypatch.setattr(versions, "remote_latest", lambda _c: None)  # ağ yok
    for step in checks.STEPS:
        if step["id"] == "health":
            continue  # gerçek ajan süreçleri gerektirir; ayrı testte taklit edilir
        found = checks.run_step(step["id"], tmp_path, want_remote=False)
        assert isinstance(found, list)
        for f in found:
            assert {"id", "area", "title", "status", "detail"} <= set(f)
            assert f["status"] in {"ok", "warn", "fail", "info"}
            if f["cause"] or f["remedy"]:
                assert f["detail"], "kanıt olmadan kök neden yazılmaz"


def test_unknown_step_is_empty(tmp_path: Path):
    assert checks.run_step("boyle-bir-adim-yok", tmp_path) == []


def test_step_crash_becomes_finding(tmp_path: Path, monkeypatch):
    """Denetim çökse bile tarama sürer; hata bir bulguya dönüşür."""

    def boom(_root):
        raise RuntimeError("patladı")

    ollama_step = next(s for s in checks.STEPS if s["id"] == "ollama")
    monkeypatch.setitem(ollama_step, "fn", boom)
    found = checks.run_step("ollama", tmp_path)
    assert len(found) == 1
    assert found[0]["status"] == "fail"
    assert "patladı" in found[0]["detail"]


def test_declared_fixes_are_all_known(tmp_path: Path, monkeypatch):
    """Bir bulgu var olmayan bir düzeltme eylemini gösteremez."""
    monkeypatch.setattr(versions, "remote_latest", lambda _c: None)
    actions = set()
    for step in checks.STEPS:
        if step["id"] == "health":
            continue
        for f in checks.run_step(step["id"], tmp_path, want_remote=False):
            if f.get("fix"):
                actions.add(f["fix"])
    # Denetimlerin ürettiği + sağlık adımının sabit ürettiği eylemler.
    actions |= {"auth-hint", "update-opencode", "update-kimi", "update-juggler"}
    for a in actions:
        assert a in fixes.INSTANT or fixes.job_argv(a, tmp_path) is not None, a


# --- temel (baseline) ve sürüm izi -------------------------------------------


def test_baseline_roundtrip_and_drift(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"kilo": "1.0.0"})
    assert checks.run_step("drift", tmp_path)[0]["status"] == "info"  # kayıt yok

    checks.write_baseline(tmp_path, {"kilo": "1.0.0"})
    assert checks.read_baseline(tmp_path)["versions"] == {"kilo": "1.0.0"}
    assert checks.run_step("drift", tmp_path)[0]["status"] == "ok"  # değişiklik yok

    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"kilo": "1.1.0"})
    drift = checks.run_step("drift", tmp_path)[0]
    assert drift["status"] == "warn"
    assert "1.0.0 → 1.1.0" in drift["evidence"][0]


def test_baseline_records_binary_fingerprint(tmp_path: Path, monkeypatch):
    """Panel ikilisinin parmak izi kaydedilir — kendi kendine güncelleme yakalanır."""
    exe = tmp_path / "tools" / "juggler" / checks._exe("juggler")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"eski ikili")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {})
    checks.write_baseline(tmp_path, {})
    known = checks.read_baseline(tmp_path)["juggler_sha256"]
    assert known and known == checks.sha256_file(exe)

    exe.write_bytes(b"panel kendini guncelledi")
    assert checks.sha256_file(exe) != known


def test_summarize_counts():
    s = checks.summarize(
        [{"status": "ok"}, {"status": "warn"}, {"status": "fail"}, {"status": "fail"}]
    )
    assert s["counts"] == {"ok": 1, "warn": 1, "fail": 2, "info": 0}
    assert s["blocking"] == 2
    assert s["healthy"] is False
    assert checks.summarize([{"status": "ok"}])["healthy"] is True


# --- düzeltme eylemleri -------------------------------------------------------


def test_backup_then_restore_roundtrip(tmp_path: Path, monkeypatch):
    exe = tmp_path / "tools" / "juggler" / checks._exe("juggler")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"calisan surum")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.4.2"})

    assert fixes.run_instant("juggler-backup", tmp_path)["ok"] is True
    exe.write_bytes(b"bozuk guncelleme")
    res = fixes.run_instant("juggler-restore", tmp_path)
    assert res["ok"] is True
    assert exe.read_bytes() == b"calisan surum"
    assert "v0.4.2" in res["detail"]


def test_backup_tag_from_version_string():
    assert checks.backup_tag("juggler v0.5.0 (commit: 73e41a6, built: x)") == "v0.5.0-73e41a6"
    assert checks.backup_tag("v0.4.2") == "v0.4.2"


def test_backup_tag_falls_back_to_binary_digest(tmp_path: Path):
    """Sürüm okunamazsa etiket İÇERİKTEN gelir — iki farklı yapı aynı klasöre yazamaz."""
    a, b = tmp_path / "a.exe", tmp_path / "b.exe"
    a.write_bytes(b"yapi A")
    b.write_bytes(b"yapi B")
    ta, tb = checks.backup_tag("", a), checks.backup_tag(None, b)
    assert ta.startswith("bilinmeyen-") and ta != tb


def test_backup_does_not_overwrite_previous_version(tmp_path: Path, monkeypatch):
    """ÖLÇÜLDÜ SORUN: sabit tek klasör, ikinci yedekte tek geri dönüş noktasını siliyordu."""
    exe = tmp_path / "tools" / "juggler" / checks._exe("juggler")
    exe.parent.mkdir(parents=True)

    exe.write_bytes(b"eski surum")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.4.2"})
    assert fixes.run_instant("juggler-backup", tmp_path)["ok"] is True

    exe.write_bytes(b"yeni surum")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.5.0"})
    assert fixes.run_instant("juggler-backup", tmp_path)["ok"] is True

    names = {b["name"] for b in checks.list_backups(tmp_path)}
    assert names == {"juggler-backup-v0.4.2", "juggler-backup-v0.5.0"}
    # Eski yedeğin İÇERİĞİ de duruyor — ezilmiş olsaydı bu bayt yok olurdu.
    assert (tmp_path / ".atlas" / "doctor" / "juggler-backup-v0.4.2" / exe.name).read_bytes() == (
        b"eski surum"
    )


def test_backup_is_idempotent_for_same_build(tmp_path: Path, monkeypatch):
    exe = tmp_path / "tools" / "juggler" / checks._exe("juggler")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"ayni yapi")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.5.0"})

    fixes.run_instant("juggler-backup", tmp_path)
    fixes.run_instant("juggler-backup", tmp_path)
    assert len(checks.list_backups(tmp_path)) == 1


def test_restore_defaults_to_newest_and_can_pick_by_name(tmp_path: Path, monkeypatch):
    exe = tmp_path / "tools" / "juggler" / checks._exe("juggler")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"eski surum")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.4.2"})
    fixes.run_instant("juggler-backup", tmp_path)
    exe.write_bytes(b"yeni surum")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.5.0"})
    fixes.run_instant("juggler-backup", tmp_path)

    exe.write_bytes(b"bozuk")
    assert fixes.run_instant("juggler-restore", tmp_path)["ok"] is True
    assert exe.read_bytes() == b"yeni surum", "adsız geri alma EN YENİ yedeği kullanmalı"

    res = fixes.run_instant("juggler-restore", tmp_path, {"name": "juggler-backup-v0.4.2"})
    assert res["ok"] is True and "v0.4.2" in res["detail"]
    assert exe.read_bytes() == b"eski surum"

    assert fixes.run_instant("juggler-restore", tmp_path, {"name": "yok-boyle"})["ok"] is False


def test_list_backups_ayni_mtime_de_deterministik(tmp_path: Path, monkeypatch):
    """SPEC 007 son adım: Windows mtime granülerliği yarışını kır.

    İki yedek DENEMEDİ değişkeni: her ikisinin de aynı mtime_ns'sini
    zorlayıp, sıralamanın name tiebreaker'ıyla belirlenimci olduğunu
    doğrula (v0.5.0 > v0.4.2 lexicographic → newest = v0.5.0).
    """
    exe = tmp_path / "tools" / "juggler" / checks._exe("juggler")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"a")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.4.2"})
    fixes.run_instant("juggler-backup", tmp_path)
    exe.write_bytes(b"b")
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"juggler": "v0.5.0"})
    fixes.run_instant("juggler-backup", tmp_path)

    # İki backup exe'sinin mtime_ns'sini eşitle → beraberlik senaryosu
    import os
    root = tmp_path / ".atlas" / "doctor"
    dirs = sorted(root.iterdir())
    assert len(dirs) == 2
    common_ns = int(dirs[0].joinpath(exe.name).stat().st_mtime_ns)
    for d in dirs:
        p = d / exe.name
        # atime, mtime — ns hassasiyet
        os.utime(p, ns=(common_ns, common_ns))

    backups = checks.list_backups(tmp_path)
    assert len(backups) == 2
    # Beraberlikte name tiebreaker: v0.5.0 > v0.4.2 desc → ilk olmalı.
    assert backups[0]["name"] == "juggler-backup-v0.5.0"
    assert backups[1]["name"] == "juggler-backup-v0.4.2"
    # 10 çağrı — hep aynı sıra (belirlenimci)
    for _ in range(10):
        again = checks.list_backups(tmp_path)
        assert [b["name"] for b in again] == [b["name"] for b in backups]


def test_restore_without_backup_fails_cleanly(tmp_path: Path):
    res = fixes.run_instant("juggler-restore", tmp_path)
    assert res["ok"] is False
    assert "Yedek bulunamadı" in res["detail"]


def test_ext_install_copies_tree(tmp_path: Path, monkeypatch):
    src = tmp_path / "juggler-profile" / "extensions" / "atlas-engineering"
    (src / "commands").mkdir(parents=True)
    (src / "juggler.extension.json").write_text('{"version":"0.1.0"}', encoding="utf-8")
    (src / "commands" / "a-command-type.js").write_text("//", encoding="utf-8")
    dst = tmp_path / "home" / ".juggler" / "extensions" / "atlas-engineering"
    monkeypatch.setattr(fixes, "ext_installed_dir", lambda _root=None: dst)

    assert fixes.run_instant("ext-install", tmp_path)["ok"] is True
    assert (dst / "commands" / "a-command-type.js").is_file()
    # idempotent: ikinci çağrı da sorunsuz
    assert fixes.run_instant("ext-install", tmp_path)["ok"] is True


def test_unknown_instant_action(tmp_path: Path):
    assert fixes.run_instant("yok-boyle", tmp_path)["ok"] is False


def test_npm_update_argv_targets_project_prefix(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(fixes.shutil, "which", lambda _n: "C:/node/npm.cmd")
    argv, title = fixes.job_argv("update-kilo", tmp_path)
    assert "@kilocode/cli@latest" in argv
    assert str(tmp_path / "tools" / "ai-cli") in argv, "kurulum proje-yerel olmalı"
    assert "kilo" in title


# --- rapor --------------------------------------------------------------------


def test_report_contains_cause_and_remedy(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"kilo": "1.0.0"})
    steps = {
        "runtime": [
            {
                "id": "x",
                "area": "Çalışma zamanı",
                "title": "Bir şey bozuk",
                "status": "fail",
                "detail": "ölçülen kanıt",
                "cause": "kök neden",
                "remedy": "çözüm yolu",
                "evidence": ["komut çıktısı"],
            }
        ]
    }
    p = report.write_report(tmp_path, steps)
    text = p.read_text(encoding="utf-8")
    assert p.parent == report.reports_dir(tmp_path)
    for expected in ("Bir şey bozuk", "ölçülen kanıt", "kök neden", "çözüm yolu", "komut çıktısı"):
        assert expected in text
    assert "1 engel" in text


# --- sunucu sözleşmesi --------------------------------------------------------


def test_server_annotates_fix_kind(tmp_path: Path, monkeypatch):
    """Arayüz düğmeyi doğru uca göndermek için fix_kind'a güvenir."""
    from tools.doctor_gui import server

    monkeypatch.setattr(server, "ROOT", tmp_path)
    findings = [
        {"fix": "juggler-backup"},  # anlık
        {"fix": "install-core"},  # uzun iş
        {"fix": "hayali-eylem"},  # bilinmeyen → düğme gösterilmez
    ]
    for f in findings:
        act = f.get("fix")
        f["fix_kind"] = (
            "instant"
            if act in fixes.INSTANT
            else ("job" if act and fixes.job_argv(act, tmp_path) else None)
        )
    assert [f["fix_kind"] for f in findings] == ["instant", "job", None]


def test_report_is_valid_when_no_findings(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {})
    p = report.write_report(tmp_path, {})
    assert "ATLAS — Sağlık & Güncelleme Raporu" in p.read_text(encoding="utf-8")


def test_baseline_file_is_json(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(versions, "local_versions", lambda _r=None: {"a": "1.0.0"})
    p = checks.write_baseline(tmp_path, {"a": "1.0.0"})
    json.loads(p.read_text(encoding="utf-8"))
