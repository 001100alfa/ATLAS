# Görev 130 — İhtiyaç

SPEC 097 `atlas doctor --diff-history-all --strict` mevcut (regresyon →
exit 9). SPEC 100 workflow diff-history-all artifact üretiyor ama
`--strict` ile regresyon gate çekmiyor. Yeni step: tarihçe varsa
--strict çalıştır, regresyon → workflow fail.

## Kabul

- `.github/workflows/atlas-doctor.yml` yeni step: `Doctor history
  regression gate (SPEC 097/130)`.
- Tarihçe var mı kontrolü: `test -d .atlas/doctor-history && ls
  .atlas/doctor-history/*.json 2>/dev/null | head -1`.
- Varsa `atlas doctor --diff-history-all --strict` → rc 9 = regresyon
  → step fail (workflow fail; `continue-on-error` YOK).
- Tarihçe yoksa skip (mevcut auto-baseline kalıbı).
- Mevcut diff-history-all artifact üretimi step'i DOKUNULMADI.
