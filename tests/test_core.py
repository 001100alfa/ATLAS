"""Referans değerler el hesabıyla türetilmiştir (SI-mm).

Kaynaklı I 200x200x9x15:
  A = 2*200*15 + 170*9 = 7530 mm²
  Iy = 2*(200*15³/12 + 3000*92.5²) + 9*170³/12 = 55 134 750 mm⁴
  Iz = 2*(15*200³/12) + 170*9³/12 = 20 010 327.5 mm⁴
  Wpl_y = 200*15*185 + 9*170²/4 = 620 025 mm³
Kutu 200x300x10:
  A = 300*200 - 280*180 = 9600 mm²
  Iy = (300*200³ - 280*180³)/12 = 63 920 000 mm⁴
"""
import math

import pytest

from sections import SectionError, box_section, i_section

REL = 1e-9  # analitik formül -> makine hassasiyeti


class TestISection:
    def test_referans_degerler(self):
        p = i_section(h=200, b=200, tw=9, tf=15)
        assert math.isclose(p.A, 7530.0, rel_tol=REL)
        assert math.isclose(p.Iy, 55_134_750.0, rel_tol=REL)
        assert math.isclose(p.Iz, 20_010_327.5, rel_tol=REL)
        assert math.isclose(p.Wel_y, 551_347.5, rel_tol=REL)
        assert math.isclose(p.Wpl_y, 620_025.0, rel_tol=REL)

    def test_agirlik(self):
        p = i_section(h=200, b=200, tw=9, tf=15)
        assert math.isclose(p.weight_kg_m, 7530e-6 * 7850, rel_tol=REL)

    def test_plastik_elastikten_buyuk(self):
        p = i_section(h=1000, b=300, tw=12, tf=20)
        assert p.Wpl_y > p.Wel_y  # şekil faktörü > 1 olmalı

    @pytest.mark.parametrize("kwargs", [
        {"h": 200, "b": 200, "tw": 9, "tf": 0},      # sıfır boyut
        {"h": 200, "b": 200, "tw": -9, "tf": 15},    # negatif
        {"h": 30, "b": 200, "tw": 9, "tf": 15},      # gövde <= 0
        {"h": 200, "b": 8, "tw": 9, "tf": 15},       # tw >= b
    ])
    def test_gecersiz_geometri(self, kwargs):
        with pytest.raises(SectionError):
            i_section(**kwargs)


class TestBoxSection:
    def test_referans_degerler(self):
        p = box_section(h=200, b=300, t=10)
        assert math.isclose(p.A, 9600.0, rel_tol=REL)
        assert math.isclose(p.Iy, 63_920_000.0, rel_tol=REL)
        assert math.isclose(p.Wel_y, 639_200.0, rel_tol=REL)

    def test_gecersiz_et_kalinligi(self):
        with pytest.raises(SectionError):
            box_section(h=200, b=300, t=100)  # hi = 0


class TestCLI:
    def test_i_kesit_calisir(self, capsys):
        from sections.cli import main
        assert main(["i", "--h", "200", "--b", "200", "--tw", "9", "--tf", "15"]) == 0
        assert "7530.0" in capsys.readouterr().out

    def test_hatali_girdi_exit_2(self, capsys):
        from sections.cli import main
        assert main(["box", "--h", "200", "--b", "300", "--t", "100"]) == 2
        assert "HATA" in capsys.readouterr().err

    def test_json_cikti(self, capsys):
        import json

        from sections.cli import main
        rc = main(["i", "--h", "200", "--b", "200", "--tw", "9", "--tf", "15", "--json"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["type"] == "i"
        assert math.isclose(data["properties"]["A"], 7530.0, rel_tol=REL)
        assert data["units"]["Iy"] == "mm4"
        assert set(data["properties"]) == {
            "A", "Iy", "Iz", "Wel_y", "Wel_z", "Wpl_y", "weight_kg_m"
        }

    def test_json_hata_stderr(self, capsys):
        import json

        from sections.cli import main
        rc = main(["box", "--h", "10", "--b", "10", "--t", "20", "--json"])
        assert rc == 2
        assert "error" in json.loads(capsys.readouterr().err)
