# 016.1 — Ship

## Sonuç
ACP client-provided method desteği eklendi — agent JSON-RPC **request**
gönderirse (`method + id`) `_call_acp` cevap yazıyor:

- **`fs/read_text_file`** — proje kökü altında güvenli okuma
  (traversal engelli); `params.line` + `params.limit` opsiyonel
  satır aralığı.
- **Yazma/shell metotları** (`fs/write_text_file`, `terminal/create`,
  `terminal/output`, `terminal/wait_for_exit`, `terminal/kill`,
  `terminal/release`) → `-32000 not supported` error.
- **Bilinmeyen method** → JSON-RPC standart `-32601 Method not found`.

SPEC 016 `session/update` `tool_call` **notification** davranışı
(sert red → `LLMPlannerError`) korundu — request/notification ayrımı
(`id` alanı var mı?) net.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +pathlib.Path import,
                                            +_ACP_READ/WRITE_METHODS sabitleri,
                                            +_acp_handle_client_request,
                                            +_acp_fs_read_response,
                                            +_resolve_project_path,
                                            _call_acp okuma döngüsü request tanıma)
tests/test_planner_acp.py                 (+6 test — happy read,
                                            traversal red, dosya yok,
                                            write red, bilinmeyen -32601,
                                            tool_call notif hala red)
pipeline/tasks/016-1-acp-fs-read/*.md     (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_acp` sözleşmesi korundu — sadece dispatcher genişledi.
- `LLMPlannerError` mevcut sınıf; yeni exception YOK.
- 016 tool_call notif red bit-uyumlu (yeni test regresyon güvencesi).

## Kalite kapıları
- pytest: **460 passed** (454 → +6)
- mypy strict + ruff: temiz

## Branch
`feat/016.1-acp-fs-read` — 015.1 üstünde tek commit.

## Notlar
- Proje kökü sabit `os.getcwd()`; test tarafında `monkeypatch.chdir(
  tmp_path)` ile izole ediliyor.
- Yol çözümü `Path.resolve()` + `relative_to(root)` — symlink/`..`
  bileşenleri güvenli.
- `fs/read_text_file` `params.line` 1-tabanlı (ACP sözleşmesi);
  `params.limit` verilmezse tümü.

## Bekleyen
- 016.2: `session/request_permission` — permission dialog
- 016.3: `fs/write_text_file` opt-in (`ATLAS_ACP_ALLOW_WRITE`)
- 016.4: MCP forwarding
- 016.5: terminal/create sandbox
