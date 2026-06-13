import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hashSkillDir, computeLock, compareLock, stableStringify } from '../lib/lockfile.js';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
const alpha = path.join(fixtures, 'layer-a', 'skills', 'core', 'alpha');

test('stableStringify sorts keys recursively', () => {
  assert.equal(
    stableStringify({ b: 1, a: { d: 2, c: 3 } }, 0),
    '{"a":{"c":3,"d":2},"b":1}',
  );
});

test('hashSkillDir is deterministic and content-sensitive', () => {
  const h1 = hashSkillDir(alpha);
  assert.equal(h1, hashSkillDir(alpha));
  assert.match(h1, /^sha256:[0-9a-f]{64}$/);

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'geno-test-'));
  try {
    fs.cpSync(alpha, dir, { recursive: true });
    assert.equal(hashSkillDir(dir), h1);
    fs.appendFileSync(path.join(dir, 'SKILL.md'), 'x');
    assert.notEqual(hashSkillDir(dir), h1);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

function makeLock(overrides = {}) {
  const manifest = {
    name: 'env', version: '1', layers: ['./layer-a'],
    install: ['core/alpha'], exclude: [], targets: ['claude'],
    ...overrides.manifest,
  };
  const layers = [{ source: './layer-a', type: 'local', name: 'layer-a', commit: null }];
  const skills = overrides.skills ?? [
    { id: 'core/alpha', layer: { name: 'layer-a' }, path: alpha },
  ];
  return computeLock(manifest, layers, skills);
}

test('computeLock has no timestamps and is reproducible byte-for-byte', () => {
  const a = stableStringify(makeLock());
  const b = stableStringify(makeLock());
  assert.equal(a, b);
  assert.equal(a.includes('time'), false);
});

test('compareLock reports changed, added, removed and manifest drift', () => {
  const base = makeLock();

  assert.equal(compareLock(base, makeLock()).drifted, false);

  const moreSkills = makeLock({
    skills: [
      { id: 'core/alpha', layer: { name: 'layer-a' }, path: alpha },
      { id: 'core/shared', layer: { name: 'layer-a' }, path: path.join(fixtures, 'layer-a', 'skills', 'core', 'shared') },
    ],
  });
  const added = compareLock(base, moreSkills);
  assert.equal(added.drifted, true);
  assert.deepEqual(added.changes, [{ id: 'core/shared', kind: 'added' }]);

  const removed = compareLock(moreSkills, base);
  assert.deepEqual(removed.changes, [{ id: 'core/shared', kind: 'removed' }]);

  const manifestDrift = compareLock(base, makeLock({ manifest: { exclude: ['x'] } }));
  assert.equal(manifestDrift.drifted, true);
  assert.equal(manifestDrift.manifestChanged, true);

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'geno-test-'));
  try {
    fs.cpSync(alpha, dir, { recursive: true });
    fs.appendFileSync(path.join(dir, 'SKILL.md'), 'mutated');
    const changed = compareLock(base, makeLock({
      skills: [{ id: 'core/alpha', layer: { name: 'layer-a' }, path: dir }],
    }));
    assert.deepEqual(changed.changes, [{ id: 'core/alpha', kind: 'changed' }]);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
