// ATLAS — Juggler ACP ajan config üreticisi (setup-acp-agents.cmd tarafından çağrılır).
//
// <project>/.juggler/acp.json içine kurulu AI CLI'ları ACP ajanı olarak yazar.
// Juggler ajanı `exec.LookPath(command)` + `exec.Command(command, args...)` ile
// stdio üzerinden spawn eder (kabuk yok, newline-delimited JSON-RPC). Bu yüzden:
//   - Node CLI'lar (kilo, cline): command="node", args=[<bin>, ...] — `.cmd` shim'i
//     PE olmadığından çalışmaz; bare ad PATH'te yok.
//   - Derlenmiş/Python ikilileri (opencode, goose, kimi): command=<exe mutlak yolu>.
// Taşınabilirlik: env (parent env üstüne merge) ile config/data proje-içine.
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(process.argv[2] || process.cwd());
const aicli = path.join(projectRoot, 'tools', 'ai-cli');
const home = path.join(aicli, 'home');
const isWin = process.platform === 'win32';
const exe = (p) => (isWin ? `${p}.exe` : p);

// Proje-yerel home (kilo/opencode gibi $HOME veya XDG köklü yazanlar için).
function homeEnv(dir) {
  return {
    HOME: dir, USERPROFILE: dir,
    XDG_CONFIG_HOME: path.join(dir, '.config'),
    XDG_DATA_HOME: path.join(dir, '.local', 'share'),
    XDG_STATE_HOME: path.join(dir, '.local', 'state'),
    XDG_CACHE_HOME: path.join(dir, '.cache'),
  };
}
// OpenCode XDG'yi doğrudan onurlandırır (paylaşılan home kökü).
function xdgEnv(dir) {
  return {
    XDG_CONFIG_HOME: path.join(dir, 'config'),
    XDG_DATA_HOME: path.join(dir, 'data'),
    XDG_STATE_HOME: path.join(dir, 'state'),
    XDG_CACHE_HOME: path.join(dir, 'cache'),
  };
}

// Her ajan: check(varlık) -> {command, args, env}. check yoksa atlanır (uyarı).
const SPECS = {
  opencode: () => {
    const bin = path.join(aicli, 'node_modules', 'opencode-ai', 'bin', exe('opencode'));
    return fs.existsSync(bin) && { command: bin, args: ['acp'], env: xdgEnv(home) };
  },
  kilo: () => {
    const bin = path.join(aicli, 'node_modules', '@kilocode', 'cli', 'bin', 'kilo');
    return fs.existsSync(bin)
      && { command: 'node', args: [bin, 'acp'], env: homeEnv(path.join(home, 'kilo-home')) };
  },
  cline: () => {
    const bin = path.join(aicli, 'node_modules', 'cline', 'bin', 'cline');
    return fs.existsSync(bin)
      && { command: 'node', args: [bin, '--acp'], env: homeEnv(path.join(home, 'cline-home')) };
  },
  kimi: () => {
    const bin = path.join(aicli, 'py-venv', isWin ? 'Scripts' : 'bin', exe('kimi'));
    return fs.existsSync(bin)
      && { command: bin, args: ['acp'], env: homeEnv(path.join(home, 'kimi-home')) };
  },
  goose: () => {
    const bin = path.join(projectRoot, 'tools', 'goose', 'goose-package', exe('goose'));
    return fs.existsSync(bin)
      && { command: bin, args: ['acp'], env: homeEnv(path.join(projectRoot, 'tools', 'goose', 'home')) };
  },
};

const agents = {};
for (const [name, resolve] of Object.entries(SPECS)) {
  const spec = resolve();
  if (spec) agents[name] = spec;
  else console.warn(`[atla] ${name}: kurulu değil — setup-ai-cli.cmd çalıştırın.`);
}

const jugglerDir = path.join(projectRoot, '.juggler');
fs.mkdirSync(jugglerDir, { recursive: true });
const acpPath = path.join(jugglerDir, 'acp.json');

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
console.log(`ACP ajanları: ${Object.keys(doc.acpAgents).join(', ') || '(hiç)'}`);
