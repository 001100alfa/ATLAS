# Görev 126 — İhtiyaç

SPEC 029/059/064/068 alarm tetiklendiğinde stderr'e UYARI + exit 8
+ (opsiyonel) SMTP/webhook/slack POST. Kalıcı log YOK — geçmişe
bakılmıyor. `.atlas/alert-history.jsonl` NDJSON append log gerek.

## Kabul

- `atlas metrics --alert PCT --alert-history [PATH]`.
- `PATH` verilmezse default `.atlas/alert-history.jsonl`.
- Alert tetiklendiğinde tek satır JSON append edilir:
  ```
  {
    "ts": "2026-08-06T14:30:00",  # ISO 8601 (datetime.now)
    "alert": "cache-hit",
    "hit_ratio_pct": 12.3,
    "threshold_pct": 30.0,
    "records": N, "tokens_in", "tokens_out",
    "cache_creation", "cache_read",
    "channels": ["email","webhook","slack"]  # verilen bayraklar
  }
  ```
- Yazma hatası SESSİZ (stderr'e UYARI ama exit 8 döner; alert
  öncelikli).
- Parent dir auto-mkdir.
- `--alert-history` YOK → SPEC 029/059/064/068 BİT-UYUMLU (log yok).
- Alert tetiklenmezse (hit_ratio >= threshold) hiçbir satır yazılmaz.
