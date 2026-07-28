# 005 — SPEC: GBrain SQLite-FTS indeksi

**Sözleşme değişmezliği:** `GBrain.remember/recall/context_for/log_event`
imzaları korunur. `Recall` dataclass alanları (name/score/snippet) korunur.

## 1. Fonksiyonel Gereksinimler

- **FR1 — İndeks dosyası:** `.atlas/gbrain.sqlite` (yol
  `ATLAS_GBRAIN_INDEX` env ile geçersiz kılınabilir). Şema:
  ```sql
  CREATE VIRTUAL TABLE notes USING fts5(
      name UNINDEXED, body,
      tokenize='unicode61 remove_diacritics 2'
  );
  CREATE TABLE meta(
      name TEXT PRIMARY KEY,
      path TEXT NOT NULL,
      mtime_ns INTEGER NOT NULL,
      sha256 TEXT NOT NULL
  );
  CREATE TABLE state(k TEXT PRIMARY KEY, v TEXT NOT NULL);
  ```
  `state` içinde `schema_version=1`.

- **FR2 — Stale tespiti:** `_is_stale()` şu koşullardan biri varsa True:
  (a) indeks dosyası yok, (b) meta boş, (c) vault'ta meta'da olmayan
  `.md` var, (d) meta'daki bir yol vault'ta yok, (e) meta.mtime_ns ile
  dosya mtime_ns uyuşmuyor. mtime doğru diyorsa sha256 kontrol edilmez
  (hızlı yol); mtime uyuşmazsa sha256 ile teyit edilir (mtime hilesine
  karşı sağlamlık).

- **FR3 — Otomatik reindex:** `recall()` çağrısı başında `_ensure_fresh()`
  çağrılır. Stale ise sessizce reindex (partial: yalnız değişen/yeni
  dosyalar; tamamen boşsa full).

- **FR4 — `remember()` uçları:** `remember()` mevcut vault yazımını
  bitirdikten sonra ilgili notun indeks kaydını **doğrudan upsert eder**
  (stale tespitine bırakmaz — yazma yolunda deterministik).

- **FR5 — `recall()` skorlaması:**
  ```
  final_score = fts_rank_score + W_TITLE * title_hit + W_NEIGHBOR * neighbor_hit
  ```
  - `fts_rank_score`: SQLite `bm25(notes)` ters işaretiyle
    normalize (0..1 aralığına indirilir).
  - `W_TITLE = 3.0`, `W_NEIGHBOR = 0.5` (mevcut sabitler korunur).
  - Snippet: SQLite `snippet(notes, 1, '', '', ' ... ', 20)` — mevcut
    "eşleşen ilk satır" davranışıyla uyumlu görünen tek satır.

- **FR6 — Graf komşuluğu:** Mevcut `Vault.graph().neighbors()` API'si
  korunur; GBrain reindex sırasında graf'ı bir kez okur, komşu araması
  bellekteki `Graph` üzerinden yapılır (disk yok).

- **FR7 — CLI:** `atlas reindex [--full]` komutu.
  - `--full`: mevcut indeksi siler, sıfırdan kurar.
  - Varsayılan: partial reindex; değişmemiş dosyalar dokunulmaz.
  - Çıktı: `indexed=N, skipped=M, removed=K, elapsed=Xs`.

- **FR8 — Geri uyumluluk:** Eski `recall()` sözleşmesi (query→list[Recall])
  aynen çalışır. `sqlite3` mevcut değilse veya FTS5 desteklenmezse
  otomatik olarak eski O(N·M) yola düşer (fallback), uyarı stderr'e
  yazılır.

- **FR9 — Boş sorgu:** Boş / sadece stopword / tek karakter sorgu →
  eski davranış (boş liste), FTS'e gidilmez.

## 2. Arayüz Sözleşmeleri

```
src/atlas_core/memory/gbrain_index.py            (yeni)
  class GBrainIndex:
      def __init__(self, vault: Vault, db_path: Path) -> None
      def ensure_fresh(self) -> tuple[int, int, int]   # (indexed, skipped, removed)
      def rebuild(self) -> tuple[int, int, int]         # full
      def upsert(self, name: str) -> None               # tek not
      def search(self, query: str, limit: int) -> list[tuple[str, float, str]]
                                                        # (name, rank, snippet)
      def is_fts_available(self) -> bool                # sqlite/fts5 kontrolü

src/atlas_core/memory/gbrain.py                  (edit)
  class GBrain:
      # __init__ imzası genişler: index_path: Path | None = None
      # remember/recall içi FTS yolunu kullanır; fallback korunur
```

## 3. Kabul Kriterleri

- **AC1 — Happy recall:** 5 notlu vault'ta `recall("kelime")` FTS
  yolundan doğru sonuç döner; skor > 0; snippet dolu.
- **AC2 — Stale otomatik reindex:** Yeni not vault'a düz dosya olarak
  eklendikten sonra `recall()` onu bulur (arada manuel reindex çağrısı
  YOK).
- **AC3 — mtime hilesi:** Dosya değiştirilip mtime elle geriye alınsa
  bile içerik değiştiği için sha256 uyuşmazlığı yakalar, reindex olur.
- **AC4 — Silinen not:** Vault'tan .md silinince reindex'te meta'dan da
  düşer; `recall` onu döndürmez.
- **AC5 — Graf komşusu:** Doğrudan eşleşmeyen ama eşleşen notun linkli
  komşusu W_NEIGHBOR skoruyla sonuçlarda görünür (mevcut davranış korundu).
- **AC6 — Fallback:** `is_fts_available()==False` durumu monkeypatch
  ile simüle edilirse `recall()` eski O(N·M) yolundan sonuç döner
  (regresyon).
- **AC7 — `atlas reindex`:** komut exit 0, sayıları yazar; `--full`
  bayrağı meta tabloyu sıfırlar.
- **AC8 — Regresyon:** mevcut `test_platform.py::test_gbrain_recall_*`
  ve `test_core.py::test_recall_graph_neighbor` yeşil kalır.
- **AC9 — Performans (smoke):** 200 sentetik notta `recall()` < 50 ms
  (test skip'lenmez ama flaky-tolerant).

## 4. Q → Kararlar

- **Q1 — Tam sözleşme değiştir mi genişlet mi?** → **Genişlet.**
  `GBrain.__init__` opsiyonel `index_path` alır; eski çağrılar (`GBrain(vault_root)`)
  aynen çalışır — index_path yoksa `.atlas/gbrain.sqlite`.
- **Q2 — Reindex ne zaman tetiklensin?** → **`recall()` başında lazy.**
  `remember()` upsert yapar. Ayrıca `atlas reindex` manuel kapı.
- **Q3 — mtime yeterli mi, hash şart mı?** → **mtime hızlı yol, hash
  emniyet.** mtime uyuşuyorsa hash atlanır (hız); mtime farklıysa hash
  ile teyit edilir (mtime hilesine karşı). Full rebuild'de hep hash.
- **Q4 — Test veritabanı in-memory mi dosya mı?** → **Her testte
  `tmp_path/gbrain.sqlite`.** In-memory FTS bazı sürümlerde farklı
  davranıyor; dosya versiyonu prod'la eşit koşul.
