"""Platform katmanı testleri.

Kapsam: vault+graf (beyin), audit hash zinciri (güvenlik),
P-A-O-R döngüsü + bütçe (orkestratör), YAML motoru (workflow).
"""
from pathlib import Path

import pytest

from atlas_core.memory.archive import archive_task
from atlas_core.memory.vault import Vault, VaultError
from atlas_core.orchestrator.core import (
    AgentRegistry,
    AgentSpec,
    BudgetExceededError,
    CallBudget,
    run_loop,
)
from atlas_core.security.audit import AuditLog, scan_secrets
from atlas_core.workflows.engine import WorkflowEngine, WorkflowError


class TestVaultGraph:
    def test_wikilink_grafi_ve_backlink(self, tmp_path: Path):
        v = Vault(tmp_path)
        v.write("wagon", "Bkz [[kesit]] ve [[EN-12663]] #demiryolu")
        v.write("kesit", "I-kesit hesabı. [[EN-12663]]")
        v.write("EN-12663", "Standart notu.")
        g = v.graph()
        assert g.nodes["wagon"].links == ("kesit", "EN-12663")
        assert g.backlinks("EN-12663") == ["kesit", "wagon"]
        assert "demiryolu" in g.nodes["wagon"].tags

    def test_neighbors_iki_yonlu(self, tmp_path: Path):
        v = Vault(tmp_path)
        v.write("a", "[[b]]")
        v.write("b", "")
        v.write("c", "[[b]]")
        assert v.graph().neighbors("b") == {"a", "c"}

    def test_orphan_tespiti(self, tmp_path: Path):
        v = Vault(tmp_path)
        v.write("bagli", "[[hedef]]")
        v.write("hedef", "")
        v.write("yalniz", "kimseyle bağlantısız")
        assert v.graph().orphans() == ["yalniz"]

    def test_gecersiz_ad_reddedilir(self, tmp_path: Path):
        with pytest.raises(VaultError):
            Vault(tmp_path).write("../kacis", "x")


class TestArchive:
    def test_gorev_arsivlenir_ve_vaulta_baglanir(self, tmp_path: Path):
        task = tmp_path / "tasks" / "002"
        task.mkdir(parents=True)
        (task / "NEED-002.md").write_text("ihtiyaç", encoding="utf-8")
        v = Vault(tmp_path / "vault")
        tar = archive_task(task, tmp_path / "archive", v, "Teslim edildi.")
        assert tar.exists() and not task.exists()
        assert "Teslim edildi" in v.read("task-002", folder="tasks")


class TestAudit:
    def test_hash_zinciri_dogrulanir(self, tmp_path: Path):
        log = AuditLog(tmp_path / "audit.jsonl")
        log.record("atlas", "plan", "ilk adım")
        log.record("atlas", "act", "ikinci adım")
        assert log.verify()

    def test_oynanmis_kayit_yakalanir(self, tmp_path: Path):
        p = tmp_path / "audit.jsonl"
        log = AuditLog(p)
        log.record("atlas", "plan", "gerçek kayıt")
        p.write_text(p.read_text(encoding="utf-8").replace("gerçek", "sahte"),
                     encoding="utf-8")
        assert not log.verify()

    def test_sir_tarayici(self):
        hits = scan_secrets('api_key = "cokgizlisifre123"')
        assert hits and hits[0][0] == "generic_assignment"
        assert "cokgizlisifre123" not in hits[0][1]  # maskeli

    def test_temiz_metin(self):
        assert scan_secrets("Iy = 55_134_750  # mm4") == []


class TestOrchestrator:
    def test_registry_kayitsiz_ajani_reddeder(self):
        reg = AgentRegistry()
        reg.register(AgentSpec("tester", "test yazar", ("pytest",), 10.0))
        assert reg.names() == ["tester"]
        with pytest.raises(KeyError):
            reg.get("hayalet")

    def test_dongu_hedefe_ulasir(self, tmp_path: Path):
        audit = AuditLog(tmp_path / "a.jsonl")
        result = run_loop(
            goal="3 gözlem topla",
            plan=lambda g, h: f"gözlem-{sum(1 for k, _ in h if k == 'observe')}",
            act=lambda p: (f"sonuç:{p}", 1.0),
            judge=lambda h: sum(1 for k, _ in h if k == "observe") >= 3,
            budget=CallBudget(limit=10.0),
            audit=audit,
        )
        assert result.done and audit.verify()

    def test_butce_asimi_donguyu_durdurur(self, tmp_path: Path):
        with pytest.raises(BudgetExceededError):
            run_loop(
                goal="pahalı iş",
                plan=lambda g, h: "adım",
                act=lambda p: ("ok", 6.0),
                judge=lambda h: False,
                budget=CallBudget(limit=10.0),  # 2. adımda 12 > 10
                audit=AuditLog(tmp_path / "a.jsonl"),
            )

    def test_adim_siniri(self, tmp_path: Path):
        result = run_loop(
            goal="bitmeyen iş",
            plan=lambda g, h: "adım",
            act=lambda p: ("ok", 0.1),
            judge=lambda h: False,
            budget=CallBudget(limit=100.0),
            audit=AuditLog(tmp_path / "a.jsonl"),
            max_steps=4,
        )
        assert not result.done


class TestWorkflowEngine:
    def test_yaml_yigini_calisir_ve_auditlenir(self, tmp_path: Path):
        wf = tmp_path / "wf.yaml"
        wf.write_text(
            "name: demo\nsteps:\n"
            "  - uses: selam\n    with: {kime: dünya}\n"
            "  - uses: selam\n    with: {kime: ATLAS}\n",
            encoding="utf-8",
        )
        audit = AuditLog(tmp_path / "a.jsonl")
        eng = WorkflowEngine(audit)
        eng.register("selam", lambda w: f"merhaba {w['kime']}")
        results = eng.run(wf)
        assert [r.output for r in results] == ["merhaba dünya", "merhaba ATLAS"]
        assert audit.verify()

    def test_kayitsiz_adim_hata(self, tmp_path: Path):
        wf = tmp_path / "wf.yaml"
        wf.write_text("steps:\n  - uses: bilinmeyen\n", encoding="utf-8")
        with pytest.raises(WorkflowError):
            WorkflowEngine(AuditLog(tmp_path / "a.jsonl")).run(wf)


class TestGBrain:
    def _brain(self, tmp_path: Path):
        from atlas_core.memory.gbrain import GBrain
        b = GBrain(tmp_path / "vault")
        b.remember("wagon-projesi", "20 metre şasi, S355 çelik kiriş boyutlandırma.",
                   links=("kesit-hesabi", "EN-12663"), tags=("demiryolu",))
        b.remember("kesit-hesabi", "I-kesit Iy hesabı paralel eksen teoremi ile.")
        b.remember("EN-12663", "Araç gövdesi yapısal gereksinim standardı.")
        b.remember("bist-desk", "FastAPI WebSocket canlı veri masası.")
        return b

    def test_recall_dogrudan_ve_baslik(self, tmp_path: Path):
        b = self._brain(tmp_path)
        hits = b.recall("kesit hesabı Iy")
        assert hits[0].name == "kesit-hesabi"          # başlık + gövde eşleşmesi
        assert all(h.name != "bist-desk" or h.score < 1 for h in hits)

    def test_graf_komsusu_yuzeye_cikar(self, tmp_path: Path):
        b = self._brain(tmp_path)
        names = [h.name for h in b.recall("S355 kiriş")]
        # wagon-projesi eşleşir; komşuları (kesit, EN) doğrudan geçmese de gelir
        assert "wagon-projesi" in names
        assert "EN-12663" in names

    def test_remember_birikir_silmez(self, tmp_path: Path):
        b = self._brain(tmp_path)
        b.remember("wagon-projesi", "Ek not: buffer EN 15551.")
        text = b.vault.read("wagon-projesi", folder="entities")
        assert "S355" in text and "EN 15551" in text   # eski + yeni birlikte

    def test_context_paketi(self, tmp_path: Path):
        b = self._brain(tmp_path)
        ctx = b.context_for("wagon kiriş")
        assert ctx.startswith("## GBrain bağlamı") and "[[wagon-projesi]]" in ctx

    def test_bos_hafiza(self, tmp_path: Path):
        from atlas_core.memory.gbrain import GBrain
        b = GBrain(tmp_path / "v")
        assert "kayıtlı bağlam yok" in b.context_for("hiçyok")
