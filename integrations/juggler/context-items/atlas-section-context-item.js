// ATLAS kesit hesabı — LLM'in çağırabileceği araç (Context Item).
// Doğrulanmış EN 1993 kesit özelliklerini (SI-mm) ATLAS kütüphanesinden verir.
import ContextItem from 'juggler/context-item';

import { atlasSections } from '../lib/atlas.js';

const FIELDS = ['A', 'Iy', 'Iz', 'Wel_y', 'Wel_z', 'Wpl_y', 'weight_kg_m'];

class AtlasSectionContextItem extends ContextItem {
  static MANIFEST = {
    id: 'atlas_section',
    name: 'ATLAS Section',
    version: '1.0.0',
    description: 'Steel cross-section properties (EN 1993, SI-mm) via ATLAS',
    author: 'ATLAS',
  };

  static getToolDefinitions() {
    return [
      {
        name: 'atlas_section',
        category: 'read',
        description:
          'Compute steel cross-section properties (area A, second moments Iy/Iz, '
          + 'elastic/plastic section moduli Wel/Wpl, mass per length) for a welded '
          + 'I-section or a rectangular box section using the ATLAS engineering '
          + 'library. EN 1993 notation, SI-mm units. Deterministic, no side effects.',
        input_schema: {
          type: 'object',
          properties: {
            section: {
              type: 'string',
              enum: ['i', 'box'],
              description: "Section type: 'i' welded I-section, 'box' rectangular box",
            },
            h: { type: 'number', description: 'Overall height [mm]' },
            b: {
              type: 'number',
              description: 'Flange width (i) / overall width (box) [mm]',
            },
            tw: { type: 'number', description: 'Web thickness [mm] — I-section only' },
            tf: { type: 'number', description: 'Flange thickness [mm] — I-section only' },
            t: { type: 'number', description: 'Wall thickness [mm] — box only' },
          },
          required: ['section', 'h', 'b'],
        },
      },
    ];
  }

  async validate(toolInput) {
    const p = /** @type {Record<string, unknown>} */ (toolInput);
    if (p.section !== 'i' && p.section !== 'box') {
      return { valid: false, error: "Parameter 'section' must be 'i' or 'box'" };
    }
    const need = p.section === 'i' ? ['h', 'b', 'tw', 'tf'] : ['h', 'b', 't'];
    for (const k of need) {
      if (typeof p[k] !== 'number') {
        return { valid: false, error: `Missing or non-numeric parameter: ${k}` };
      }
    }
    return { valid: true, params: p };
  }

  async execute(params) {
    const { section } = params;
    const dims = section === 'i'
      ? { h: params.h, b: params.b, tw: params.tw, tf: params.tf }
      : { h: params.h, b: params.b, t: params.t };
    return atlasSections(section, dims);
  }

  getSummary(outcome) {
    if (!outcome.success) {
      return { summary: outcome.error || 'atlas_section failed', success: false, icon: '✗' };
    }
    const r = outcome.result;
    const { properties: pr, units: u } = r;
    const lines = [`Section: ${r.type}`, ...FIELDS.map((k) => `${k} = ${pr[k]} ${u[k]}`)];
    return { summary: lines.join('\n'), success: true, icon: '✓' };
  }
}

export default AtlasSectionContextItem;
