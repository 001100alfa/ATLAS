// Sistem-prompt katkısı — etkin yeteneklere göre modele terse, kalıcı yönerge.
// Saf fonksiyon olmalı: yalnız enabledPluginIds'e bağlı, saat/konuşma okumaz
// (önbelleklenen prompt çıpasına katılır).
export default function systemPromptContribution({ enabledPluginIds }) {
  const has = (id) => enabledPluginIds.includes(id);
  const sections = [];
  if (has('atlas_section')) {
    sections.push(
      '## ATLAS engineering\n'
      + 'For steel cross-section properties (area, second moments, section moduli, '
      + 'mass) prefer the `atlas_section` tool over hand calculation or shelling '
      + 'out — it returns verified EN 1993 values in SI-mm with explicit units.',
    );
  }
  if (has('atlas_recall')) {
    sections.push(
      '## ATLAS memory\n'
      + 'At the start of a task, use `atlas_recall` to load relevant prior '
      + 'decisions and known errors from project memory before proposing changes.',
    );
  }
  return sections.join('\n\n');
}
