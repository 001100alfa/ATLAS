"""SPEC 013 — CallBudget.charge_tokens birim testleri."""

from __future__ import annotations

import pytest

from atlas_core.orchestrator.core import BudgetExceededError, CallBudget


def test_charge_tokens_fiyat_sifir_no_op() -> None:
    """M3: fiyat 0 → cost 0, bütçe hiç değişmez."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(1000, 500, price_in=0.0, price_out=0.0)
    assert b.spent == 0.0


def test_charge_tokens_fiyat_negatif_no_op() -> None:
    """Fail-safe: negatif fiyat → no-op (011 kalıbı)."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(1000, 500, price_in=-3.0, price_out=-15.0)
    assert b.spent == 0.0


def test_charge_tokens_hesap() -> None:
    """Cost = in * price_in / 1e6 + out * price_out / 1e6."""
    b = CallBudget(limit=100.0)
    # 1M input * 3 + 200k output * 15 = 3 + 3 = 6
    b.charge_tokens(1_000_000, 200_000, price_in=3.0, price_out=15.0)
    assert b.spent == pytest.approx(6.0)


def test_charge_tokens_kismi_fiyat() -> None:
    """price_in > 0 ama price_out = 0 → yalnız input maliyeti."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(1_000_000, 500_000, price_in=3.0, price_out=0.0)
    assert b.spent == pytest.approx(3.0)


def test_charge_tokens_butce_asim() -> None:
    """Bütçe aşarsa BudgetExceededError; mevcut sınıf yeniden kullanıldı."""
    b = CallBudget(limit=1.0)  # düşük limit
    with pytest.raises(BudgetExceededError, match="llm tokens"):
        b.charge_tokens(1_000_000, 200_000, price_in=3.0, price_out=15.0)
    # Aşım → bütçe değişmez (mevcut charge() sözleşmesi)
    assert b.spent == 0.0


def test_charge_tokens_kumulatif() -> None:
    """Ardışık çağrılar birikir."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(1_000_000, 0, price_in=3.0, price_out=0.0)   # +3
    b.charge_tokens(500_000, 0, price_in=3.0, price_out=0.0)     # +1.5
    assert b.spent == pytest.approx(4.5)


def test_charge_tokens_sifir_tokens() -> None:
    """in_tok=0 out_tok=0 → cost 0, bütçe değişmez."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(0, 0, price_in=3.0, price_out=15.0)
    assert b.spent == 0.0


def test_charge_ile_charge_tokens_ayni_butce() -> None:
    """SPEC 013 sözleşme: charge ve charge_tokens aynı bütçeyi paylaşır."""
    b = CallBudget(limit=10.0)
    b.charge(5.0, "act 1")
    with pytest.raises(BudgetExceededError):
        b.charge_tokens(1_000_000, 200_000, price_in=3.0, price_out=15.0)  # +6
    # 5 + 6 = 11 > 10 → charge ilkinde 5 geçti, ikinci aşımdan reddedildi
    assert b.spent == 5.0  # ilk 5 geçti


def test_charge_ile_charge_tokens_bir_arada_gecer() -> None:
    """İkisi birlikte bütçe içinde kalırsa toplam birikir."""
    b = CallBudget(limit=100.0)
    b.charge(5.0, "act 1")
    b.charge_tokens(1_000_000, 200_000, price_in=3.0, price_out=15.0)  # +6
    assert b.spent == pytest.approx(11.0)


# ---------- SPEC 015.1: cache-hit indirim ----------


def test_015_1_cache_read_yuzde_10() -> None:
    """cache_read = %10 tam fiyat: 1M cache_read * 3 * 0.1 = 0.3."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(
        0, 0, price_in=3.0, price_out=15.0,
        cache_read=1_000_000,
    )
    assert b.spent == pytest.approx(0.3)


def test_015_1_cache_creation_yuzde_125() -> None:
    """cache_creation = %125 tam fiyat: 1M cache * 3 * 1.25 = 3.75."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(
        0, 0, price_in=3.0, price_out=15.0,
        cache_creation=1_000_000,
    )
    assert b.spent == pytest.approx(3.75)


def test_015_1_hep_bir_arada() -> None:
    """input + cache_write + cache_read + output — toplam."""
    b = CallBudget(limit=100.0)
    # 500k input * 3 = 1.5
    # 500k cache_c * 3 * 1.25 = 1.875
    # 500k cache_r * 3 * 0.1 = 0.15
    # 200k out * 15 = 3.0
    # toplam = 6.525
    b.charge_tokens(
        500_000, 200_000, price_in=3.0, price_out=15.0,
        cache_creation=500_000, cache_read=500_000,
    )
    assert b.spent == pytest.approx(6.525)


def test_015_1_default_kwargs_013_uyumlu() -> None:
    """cache_* verilmezse 013 davranışı bit-uyumlu."""
    b = CallBudget(limit=100.0)
    b.charge_tokens(1_000_000, 200_000, price_in=3.0, price_out=15.0)
    assert b.spent == pytest.approx(6.0)  # 013 hesabı aynen


def test_015_1_what_metni_cache_bilgisi() -> None:
    """Bütçe aşarsa what mesajı cache bilgisi taşır."""
    b = CallBudget(limit=0.5)
    with pytest.raises(BudgetExceededError) as exc_info:
        b.charge_tokens(
            1_000_000, 0, price_in=3.0, price_out=0.0,
            cache_creation=100_000,
        )
    msg = str(exc_info.value)
    assert "cache=100000" in msg
