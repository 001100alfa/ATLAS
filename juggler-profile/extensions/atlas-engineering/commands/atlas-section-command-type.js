// /atlas-section — kullanıcı slash komutu (LLM'siz, hızlı kesit hesabı).
//   /atlas-section i <h> <b> <tw> <tf>
//   /atlas-section box <h> <b> <t>
import CommandType from 'juggler/command-type';

import { atlasSections } from '../lib/atlas.js';

const FIELDS = ['A', 'Iy', 'Iz', 'Wel_y', 'Wel_z', 'Wpl_y', 'weight_kg_m'];
const USAGE = 'Usage: /atlas-section i <h> <b> <tw> <tf>  |  /atlas-section box <h> <b> <t>';

class AtlasSectionCommandType extends CommandType {
  static MANIFEST = {
    id: 'atlas-section',
    name: 'ATLAS Section',
    version: '1.0.0',
    description: 'Compute a steel section (I or box) via ATLAS — SI-mm, EN 1993',
  };

  async execute(args) {
    const [section, ...nums] = args;
    if (section !== 'i' && section !== 'box') {
      return { handled: true, error: USAGE };
    }
    const keys = section === 'i' ? ['h', 'b', 'tw', 'tf'] : ['h', 'b', 't'];
    if (nums.length !== keys.length) {
      return { handled: true, error: `Expected ${keys.length} numbers: ${keys.join(' ')}` };
    }
    const dims = {};
    for (let i = 0; i < keys.length; i++) {
      const v = Number(nums[i]);
      if (Number.isNaN(v)) {
        return { handled: true, error: `Not a number: ${nums[i]}` };
      }
      dims[keys[i]] = v;
    }
    try {
      const r = await atlasSections(section, dims);
      const { properties: pr, units: u } = r;
      const lines = [
        `ATLAS ${r.type}-section:`,
        ...FIELDS.map((k) => `${k} = ${pr[k]} ${u[k]}`),
      ];
      return { handled: true, message: lines.join('\n') };
    } catch (e) {
      return { handled: true, error: String((e && e.message) || e) };
    }
  }
}

export default AtlasSectionCommandType;
