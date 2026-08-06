# Görev 125 — İhtiyaç

SPEC 089 atlas-ci-status.yml drift-scan job'u `gen_ci_badges.py --check`
sonucunu sadece issue'ya yansıtıyor. Kullanıcı diff'i lokal inceleme
için indirebilmeli — upload artifact eklenmeli.

## Kabul

- `.github/workflows/atlas-ci-status.yml` yeni step:
  `Upload drift diff artifact`.
- `README.md` içeriği (regen sonrası) artifact olarak upload.
- `if: steps.check.outputs.rc != '0'` (yalnız drift varsa).
- Mevcut issue step'i DOKUNULMADI.
