// ATLAS — Juggler ACP ajan config üreticisi (setup-acp-agents.cmd tarafından çağrılır).
//
// <project>/.juggler/acp.json içine OpenCode ve Kilo'yu ACP ajanı olarak yazar.
// Juggler ajanı `exec.LookPath(command)` + `exec.Command(command, args...)` ile
// spawn eder (kabuk yok). Bu yüzden:
//   - Kilo (Node CLI): command="node" (PATH'te gerçek exe), args=[<kilo bin>, "acp"].
//     `.cmd` shim'i PE olmadığından Go exec ile çalışmaz; bare "kilo" PATH'te yok.
//   - OpenCode (derlenmiş ikili): command=<opencode.exe mutlak yolu>, args=["acp"].
// Taşınabilirlik: env (parent env üstüne merge edilir) ile config/data proje-içine.
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(process.argv[2] || process.cwd());
const aicli = path.join(projectRoot, 'tools', 'ai-cli');
const home = path.join(aicli, 'home');

const kiloBin = path.join(aicli, 'node_modules', '@kilocode', 'cli', 'bin', 'kilo');
const kiloHome = path.join(home, 'kilo-home');

const isWin = process.platform === 'win32';
const opencodeCandidates = [
  path.join(aicli, 'node_modules', 'opencode-ai', 'bin', isWin ? 'opencode.exe' : 'opencode'),
];
const opencodeExe = opencodeCandidates.find((p) => fs.existsSync(p));

const agents = {};

if (fs.existsSync(kiloBin)) {
  agents.kilo = {
    command: 'node',
    args: [kiloBin, 'acp'],
    env: { HOME: kiloHome, USERPROFILE: kiloHome },
  };
} else {
  console.warn(`[UYARI] kilo bin yok: ${kiloBin} — setup-ai-cli.cmd çalıştırın.`);
}

if (opencodeExe) {
  agents.opencode = {
    command: opencodeExe,
    args: ['acp'],
    env: {
      XDG_CONFIG_HOME: path.join(home, 'config'),
      XDG_DATA_HOME: path.join(home, 'data'),
      XDG_STATE_HOME: path.join(home, 'state'),
      XDG_CACHE_HOME: path.join(home, 'cache'),
    },
  };
} else {
  console.warn('[UYARI] opencode.exe yok — setup-ai-cli.cmd çalıştırın.');
}

const jugglerDir = path.join(projectRoot, '.juggler');
fs.mkdirSync(jugglerDir, { recursive: true });
const acpPath = path.join(jugglerDir, 'acp.json');

// Mevcut config'i koru; yalnız acpAgents.{kilo,opencode}'u güncelle.
let doc = {};
if (fs.existsSync(acpPath)) {
  try {
    doc = JSON.parse(fs.readFileSync(acpPath, 'utf8'));
  } catch {
    console.warn('[UYARI] mevcut acp.json bozuk — yeniden yazılıyor.');
  }
}
doc.acpAgents = { ...(doc.acpAgents || {}), ...agents };

fs.writeFileSync(acpPath, JSON.stringify(doc, null, 2) + '\n', 'utf8');
console.log(`Yazıldı: ${acpPath}`);
console.log(`ACP ajanları: ${Object.keys(doc.acpAgents).join(', ')}`);
