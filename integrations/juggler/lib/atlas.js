// ATLAS launcher köprüsü — kayıtlı bir yetenek DEĞİL (suffix yok), yalnız
// context-item/command dosyalarınca import edilir.
//
// ATLAS CLI'larını (`atlas`, `atlas-sections`) juggler/ops shell üzerinden
// çağırır. Launcher'lar PATH'ten çözülür — ATLAS dizinini (veya taşınabilir
// bundle'ı) PATH'e ekle. Ayrıntı: ATLAS docs/JUGGLER.md.
import { shell } from 'juggler/ops';

const TIMEOUT_MS = 30000;

/**
 * atlas-sections'ı --json ile çalıştırır, {type, properties, units} döndürür.
 * @param {'i'|'box'} section - kesit tipi
 * @param {Record<string, number>} dims - boyutlar (mm), ör. {h, b, tw, tf}
 * @returns {Promise<{type: string, properties: object, units: object}>}
 */
export async function atlasSections(section, dims) {
  const args = Object.entries(dims)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `--${k} ${Number(v)}`)
    .join(' ');
  const command = `atlas-sections ${section} ${args} --json`;
  const res = await shell({ command, timeout: TIMEOUT_MS });
  if (!res.success) {
    // atlas-sections hata JSON'unu ({"error": ...}) stderr'e yazar.
    let msg = (res.stderr || '').trim();
    try {
      msg = JSON.parse(msg).error || msg;
    } catch {
      /* JSON değilse ham mesajı bırak */
    }
    throw new Error(msg || `atlas-sections çıkış kodu ${res.exitCode}`);
  }
  return JSON.parse(res.stdout);
}

/**
 * atlas platform CLI'ının `context` alt komutuyla GBrain bağlam paketini alır.
 * @param {string} topic - konu/sorgu
 * @returns {Promise<string>} bağlam bloğu (düz metin)
 */
export async function atlasContext(topic) {
  // topic serbest metin — kabuk enjeksiyonuna karşı JSON-tırnakla.
  const command = `atlas context ${JSON.stringify(String(topic))}`;
  const res = await shell({ command, timeout: TIMEOUT_MS });
  if (!res.success) {
    throw new Error((res.stderr || '').trim() || `atlas çıkış kodu ${res.exitCode}`);
  }
  return res.stdout.trim();
}
