import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { bake, checkDrift } from '../lib/bake.js';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');

function sandbox(manifestYaml) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'geno-bake-'));
  fs.cpSync(path.join(fixtures, 'layer-a'), path.join(dir, 'layer-a'), { recursive: true });
  fs.cpSync(path.join(fixtures, 'layer-b'), path.join(dir, 'layer-b'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'geno-image.yaml'), manifestYaml);
  return dir;
}

const CLEAN_MANIFEST = `name: test-env
version: "1.0.0"

layers:
  - ./layer-a
  - ./layer-b

install:
  - core/alpha
  - core/shared
  - misc/beta
  - misc/skipme

exclude:
  - skipme

targets:
  - claude
  - opencode
  - generic
`;

test('full bake: copies skills, applies exclude, last layer wins, emits adapters, writes lock', () => {
  const dir = sandbox(CLEAN_MANIFEST);
  try {
    const events = [];
    const result = bake({ cwd: dir, onEvent: (e) => events.push(e) });

    assert.equal(result.ok, true, JSON.stringify(result.errors));
    assert.deepEqual(result.installed.map((s) => s.id), ['core/alpha', 'core/shared', 'misc/beta']);
    assert.deepEqual(result.excluded, ['misc/skipme']);

    // Last layer wins for the overlapping skill.
    const shared = fs.readFileSync(path.join(dir, 'build', 'skills', 'core', 'shared', 'SKILL.md'), 'utf8');
    assert.match(shared, /layer-b flavor/);

    // Adapters: only the three requested targets.
    assert.ok(fs.existsSync(path.join(dir, 'build', '.claude-plugin', 'plugin.json')));
    assert.ok(fs.existsSync(path.join(dir, 'build', '.opencode', 'plugins', 'test-env.js')));
    assert.ok(fs.existsSync(path.join(dir, 'build', 'plugin.json')));
    assert.equal(fs.existsSync(path.join(dir, 'build', 'gemini-extension.json')), false);

    const claude = JSON.parse(fs.readFileSync(path.join(dir, 'build', '.claude-plugin', 'plugin.json'), 'utf8'));
    assert.equal(claude.skills, './skills');
    assert.equal('installed_skills' in claude, false);
    const generic = JSON.parse(fs.readFileSync(path.join(dir, 'build', 'plugin.json'), 'utf8'));
    assert.deepEqual(generic.installed_skills, ['core/alpha', 'core/shared', 'misc/beta']);

    // Audit report exists and is clean.
    const report = JSON.parse(fs.readFileSync(path.join(dir, 'build', 'audit-report.json'), 'utf8'));
    assert.deepEqual(report.findings, []);

    // Lockfile: present and byte-identical across a second bake.
    const lockPath = path.join(dir, 'geno-image.lock');
    const first = fs.readFileSync(lockPath, 'utf8');
    bake({ cwd: dir });
    assert.equal(fs.readFileSync(lockPath, 'utf8'), first);

    // No drift right after a bake.
    assert.equal(checkDrift({ cwd: dir }).drifted, false);

    // Mutating an installed skill is detected as drift.
    fs.appendFileSync(path.join(dir, 'layer-a', 'skills', 'core', 'alpha', 'SKILL.md'), 'mutation');
    const drift = checkDrift({ cwd: dir });
    assert.equal(drift.drifted, true);
    assert.deepEqual(drift.changes, [{ id: 'core/alpha', kind: 'changed' }]);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('audit error findings block the bake; allowlist unblocks', () => {
  const blocked = sandbox(`layers:
  - ./layer-b
install:
  - misc/sketchy
`);
  try {
    const result = bake({ cwd: blocked });
    assert.equal(result.ok, false);
    assert.ok(result.errors.some((e) => e.includes('Audit blocked')));
    assert.equal(fs.existsSync(path.join(blocked, 'build', 'skills', 'misc', 'sketchy')), false);
    // The report is still written for inspection.
    const report = JSON.parse(fs.readFileSync(path.join(blocked, 'build', 'audit-report.json'), 'utf8'));
    assert.ok(report.findings.length >= 2);
  } finally {
    fs.rmSync(blocked, { recursive: true, force: true });
  }

  const allowed = sandbox(`layers:
  - ./layer-b
install:
  - misc/sketchy
audit:
  allow:
    - misc/sketchy
`);
  try {
    const result = bake({ cwd: allowed });
    assert.equal(result.ok, true, JSON.stringify(result.errors));
    assert.ok(fs.existsSync(path.join(allowed, 'build', 'skills', 'misc', 'sketchy', 'SKILL.md')));
  } finally {
    fs.rmSync(allowed, { recursive: true, force: true });
  }
});

test('missing skills fail the bake with all of them named', () => {
  const dir = sandbox(`layers:
  - ./layer-a
install:
  - core/alpha
  - core/ghost
  - misc/phantom
`);
  try {
    const result = bake({ cwd: dir });
    assert.equal(result.ok, false);
    assert.ok(result.errors.some((e) => e.includes('core/ghost') && e.includes('misc/phantom')));
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('missing layer fails before any filesystem writes', () => {
  const dir = sandbox(`layers:
  - ./no-such-layer
install:
  - core/alpha
`);
  try {
    const result = bake({ cwd: dir });
    assert.equal(result.ok, false);
    assert.ok(result.errors.some((e) => e.includes('no-such-layer')));
    assert.equal(fs.existsSync(path.join(dir, 'build')), false);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('opencode adapter is importable ESM', async () => {
  const dir = sandbox(CLEAN_MANIFEST);
  try {
    bake({ cwd: dir });
    const mod = await import(path.join(dir, 'build', '.opencode', 'plugins', 'test-env.js'));
    const config = {};
    await mod.default({ config });
    assert.equal(config.skills.paths.length, 1);
    assert.match(config.skills.paths[0], /build\/skills$/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
