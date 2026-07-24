// tools/gen-acp-config.js deterministik entegrasyon testi (node --test).
// Sahte projectRoot + stub bin dosyaları kurar, generator'ı spawn eder,
// üretilen .juggler/acp.json'u doğrular. Platform-uyumlu (isWin).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const GEN = fileURLToPath(new URL('../../tools/gen-acp-config.js', import.meta.url));
const isWin = process.platform === 'win32';
const exe = (p) => (isWin ? `${p}.exe` : p);

function mkProject() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-acp-'));
}
function touch(p) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, '');
}
// Ajan -> stub bin göreli yolu (generator'ın aradığı yollar).
function binPath(root, name) {
  const aicli = path.join(root, 'tools', 'ai-cli');
  return {
    opencode: path.join(aicli, 'node_modules', 'opencode-ai', 'bin', exe('opencode')),
    kilo: path.join(aicli, 'node_modules', '@kilocode', 'cli', 'bin', 'kilo'),
    cline: path.join(aicli, 'node_modules', 'cline', 'bin', 'cline'),
    kimi: path.join(aicli, 'py-venv', isWin ? 'Scripts' : 'bin', exe('kimi')),
    goose: path.join(root, 'tools', 'goose', 'goose-package', exe('goose')),
  }[name];
}
function run(root) {
  execFileSync('node', [GEN, root], { stdio: 'pipe' });
  return JSON.parse(fs.readFileSync(path.join(root, '.juggler', 'acp.json'), 'utf8'));
}

test('5 ajan kurulu -> hepsi doğru command/args ile yazılır', () => {
  const root = mkProject();
  for (const n of ['opencode', 'kilo', 'cline', 'kimi', 'goose']) touch(binPath(root, n));
  const doc = run(root);
  const a = doc.acpAgents;
  assert.deepEqual(Object.keys(a).sort(), ['cline', 'goose', 'kilo', 'kimi', 'opencode']);

  // Node CLI'lar: command "node", bin + bayrak
  assert.equal(a.kilo.command, 'node');
  assert.deepEqual(a.kilo.args, [binPath(root, 'kilo'), 'acp']);
  assert.equal(a.cline.command, 'node');
  assert.deepEqual(a.cline.args, [binPath(root, 'cline'), '--acp']);

  // Derlenmiş/Python ikilileri: mutlak exe yolu
  assert.equal(a.opencode.command, binPath(root, 'opencode'));
  assert.deepEqual(a.opencode.args, ['acp']);
  assert.equal(a.goose.command, binPath(root, 'goose'));
  assert.equal(a.kimi.command, binPath(root, 'kimi'));

  // env ile config proje-yerele yönlendirilir (kilo HOME override)
  assert.ok(a.kilo.env.HOME.includes('kilo-home'));
  assert.ok(a.kilo.env.USERPROFILE.includes('kilo-home'));
  // opencode XDG (paylaşılan home kökü)
  assert.ok(a.opencode.env.XDG_CONFIG_HOME.endsWith(path.join('home', 'config')));
});

test('kısmi kurulum -> yalnız kurulu ajan yazılır', () => {
  const root = mkProject();
  touch(binPath(root, 'kilo')); // yalnız kilo
  const doc = run(root);
  assert.deepEqual(Object.keys(doc.acpAgents), ['kilo']);
});

test('hiçbiri kurulu değil -> acpAgents boş', () => {
  const root = mkProject();
  const doc = run(root);
  assert.deepEqual(doc.acpAgents, {});
});

test('mevcut acp.json korunur (merge)', () => {
  const root = mkProject();
  touch(binPath(root, 'kilo'));
  const jdir = path.join(root, '.juggler');
  fs.mkdirSync(jdir, { recursive: true });
  fs.writeFileSync(
    path.join(jdir, 'acp.json'),
    JSON.stringify({ acpAgents: { custom: { command: 'x' } }, other: 1 }),
  );
  const doc = run(root);
  assert.equal(doc.other, 1, 'yabancı üst-düzey alan korunmalı');
  assert.ok(doc.acpAgents.custom, 'mevcut ajan korunmalı');
  assert.ok(doc.acpAgents.kilo, 'yeni ajan eklenmeli');
});
