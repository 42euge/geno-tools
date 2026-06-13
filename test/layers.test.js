import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { walkSkills, findSkill, readSkillMeta, readLayerMeta } from '../lib/layers.js';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
const layerA = path.join(fixtures, 'layer-a');
const layerB = path.join(fixtures, 'layer-b');

test('walkSkills lists category/name skill ids, sorted', () => {
  assert.deepEqual(walkSkills(layerA), ['core/alpha', 'core/shared']);
  assert.deepEqual(walkSkills(layerB), ['core/shared', 'misc/beta', 'misc/sketchy']);
});

test('findSkill: later layers win for overlapping skills', () => {
  const layers = [
    { name: 'layer-a', path: layerA },
    { name: 'layer-b', path: layerB },
  ];
  const hit = findSkill(layers, 'core/shared');
  assert.equal(hit.layer.name, 'layer-b');
  assert.equal(findSkill(layers, 'core/alpha').layer.name, 'layer-a');
  assert.equal(findSkill(layers, 'core/nope'), null);
});

test('readSkillMeta parses frontmatter including folded descriptions', () => {
  const meta = readSkillMeta(path.join(layerA, 'skills', 'core', 'alpha'));
  assert.equal(meta.name, 'alpha');
  assert.equal(meta.description, 'Test skill alpha. Does nothing dangerous.');
  assert.equal(meta.allowedTools, 'Read(*)');
  assert.equal(meta.error, null);
});

test('readLayerMeta reads layer.json ecosystem', () => {
  assert.equal(readLayerMeta(layerA).ecosystem, 'test-ecosystem / A');
  assert.equal(readLayerMeta('/nonexistent').ecosystem, null);
});
