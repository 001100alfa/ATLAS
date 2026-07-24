// ATLAS GBrain hafıza geri-çağırma — LLM aracı (Context Item).
// Bir konu için önceki kararları/bağlamı ATLAS beyninden getirir.
import ContextItem from 'juggler/context-item';

import { atlasContext } from '../lib/atlas.js';

class AtlasRecallContextItem extends ContextItem {
  static MANIFEST = {
    id: 'atlas_recall',
    name: 'ATLAS Recall',
    version: '1.0.0',
    description: 'Recall project context/decisions from ATLAS GBrain memory',
    author: 'ATLAS',
  };

  static getToolDefinitions() {
    return [
      {
        name: 'atlas_recall',
        category: 'read',
        description:
          'Retrieve relevant project context, prior decisions and known errors '
          + 'from the ATLAS GBrain (Obsidian-vault-backed) memory for a topic. '
          + 'Use at the start of a task to ground work in existing decisions.',
        input_schema: {
          type: 'object',
          properties: {
            topic: {
              type: 'string',
              description: 'Topic or query to recall context for',
            },
          },
          required: ['topic'],
        },
      },
    ];
  }

  async validate(toolInput) {
    const topic = /** @type {Record<string, unknown>} */ (toolInput).topic;
    if (typeof topic !== 'string' || !topic.trim()) {
      return { valid: false, error: "Parameter 'topic' must be a non-empty string" };
    }
    return { valid: true, params: toolInput };
  }

  async execute(params) {
    return { context: await atlasContext(params.topic) };
  }

  getSummary(outcome) {
    if (!outcome.success) {
      return { summary: outcome.error || 'atlas_recall failed', success: false, icon: '✗' };
    }
    return {
      summary: outcome.result.context || '(no context)',
      success: true,
      icon: '✓',
    };
  }
}

export default AtlasRecallContextItem;
