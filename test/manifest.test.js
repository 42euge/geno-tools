import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { loadManifest, saveManifest, isExcluded, KNOWN_TARGETS } from '../lib/manifest.js';

function withManifest(content, fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'geno-test-'));
  const file = path.join(dir, 'geno-image.yaml');
  fs.writeFileSync(file, content);
  try {
    return fn(file);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test('missing manifest reports an actionable error', () => {
  const { manifest, errors } = loadManifest('/nonexistent/geno-image.yaml');
  assert.equal(manifest, null);
  assert.match(errors[0], /geno init/);
});

test('a typo’d install key is a warning, not a silent empty bake', () => {
  withManifest('name: x\nversion: "1"\nlayers:\n  - ./l\ninstal:\n  - oops\n', (file) => {
    const { warnings } = loadManifest(file);
    assert.ok(warnings.some((w) => w.includes('"instal"')));
    assert.ok(warnings.some((w) => w.includes('no "install" key')));
  });
});

test('duplicate install entries are deduped with a warning', () => {
  withManifest('layers:\n  - ./l\ninstall:\n  - core/a\n  - core/a\n', (file) => {
    const { manifest, warnings } = loadManifest(file);
    assert.deepEqual(manifest.install, ['core/a']);
    assert.ok(warnings.some((w) => w.includes('Duplicate')));
  });
});

test('invalid install ids are errors', () => {
  withManifest('layers:\n  - ./l\ninstall:\n  - "bad skill name!"\n', (file) => {
    const { errors } = loadManifest(file);
    assert.ok(errors.some((e) => e.includes('Invalid install entry')));
  });
});

test('unknown targets are errors; valid targets pass', () => {
  withManifest('layers:\n  - ./l\ninstall:\n  - a\ntargets:\n  - claude\n  - vscode\n', (file) => {
    const { manifest, errors } = loadManifest(file);
    assert.ok(errors.some((e) => e.includes('Unknown target "vscode"')));
    assert.deepEqual(manifest.targets, ['claude']);
  });
});

test('targets default to all when omitted', () => {
  withManifest('layers:\n  - ./l\ninstall:\n  - a\n', (file) => {
    const { manifest } = loadManifest(file);
    assert.deepEqual(manifest.targets, KNOWN_TARGETS);
  });
});

test('audit allowlist parses', () => {
  withManifest('layers:\n  - ./l\ninstall:\n  - a\naudit:\n  allow:\n    - misc/x:curl-pipe-sh\n', (file) => {
    const { manifest, errors } = loadManifest(file);
    assert.deepEqual(errors, []);
    assert.deepEqual(manifest.audit.allow, ['misc/x:curl-pipe-sh']);
  });
});

test('exclude matches full id or bare basename', () => {
  assert.equal(isExcluded('core/geno-tools', ['geno-tools']), true);
  assert.equal(isExcluded('core/geno-tools', ['core/geno-tools']), true);
  assert.equal(isExcluded('core/geno-tools', ['misc/geno-tools']), false);
  assert.equal(isExcluded('core/geno-tools', ['geno-audit']), false);
});

test('saveManifest round-trips through loadManifest', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'geno-test-'));
  const file = path.join(dir, 'geno-image.yaml');
  try {
    saveManifest(file, {
      name: 'env', version: '2.0.0',
      layers: ['./layers/meta-geno-core'],
      install: ['core/geno-tools'],
      exclude: ['geno-dangerous-skill'],
      targets: ['claude', 'generic'],
      audit: { allow: ['core/geno-tools:broad-tools'] },
    });
    const { manifest, errors } = loadManifest(file);
    assert.deepEqual(errors, []);
    assert.equal(manifest.name, 'env');
    assert.deepEqual(manifest.install, ['core/geno-tools']);
    assert.deepEqual(manifest.targets, ['claude', 'generic']);
    assert.deepEqual(manifest.audit.allow, ['core/geno-tools:broad-tools']);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
