import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { auditSkillDir, auditSkills, isFindingAllowed } from '../lib/audit.js';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
const sketchy = path.join(fixtures, 'layer-b', 'skills', 'misc', 'sketchy');
const alpha = path.join(fixtures, 'layer-a', 'skills', 'core', 'alpha');

test('clean skill produces no findings', () => {
  assert.deepEqual(auditSkillDir(alpha, 'core/alpha'), []);
});

test('sketchy skill trips curl-pipe-sh, prompt-injection and broad-tools', () => {
  const rules = auditSkillDir(sketchy, 'misc/sketchy').map((f) => f.rule).sort();
  assert.deepEqual(rules, ['broad-tools', 'curl-pipe-sh', 'prompt-injection']);
});

test('findings carry file, line and excerpt', () => {
  const f = auditSkillDir(sketchy, 'misc/sketchy').find((x) => x.rule === 'curl-pipe-sh');
  assert.equal(f.severity, 'error');
  assert.equal(f.file, 'SKILL.md');
  assert.ok(f.line > 0);
  assert.match(f.excerpt, /curl .*\| sh/);
});

test('allowlist matches full id, basename, and skill:rule', () => {
  const finding = { skill: 'misc/sketchy', rule: 'curl-pipe-sh' };
  assert.equal(isFindingAllowed(finding, ['misc/sketchy']), true);
  assert.equal(isFindingAllowed(finding, ['sketchy']), true);
  assert.equal(isFindingAllowed(finding, ['misc/sketchy:curl-pipe-sh']), true);
  assert.equal(isFindingAllowed(finding, ['misc/sketchy:prompt-injection']), false);
  assert.equal(isFindingAllowed(finding, ['misc/other']), false);
});

test('auditSkills partitions by allowlist and severity', () => {
  const skills = [{ id: 'misc/sketchy', path: sketchy }];
  const blocked = auditSkills(skills, []);
  assert.equal(blocked.errors.length, 2);
  assert.equal(blocked.warns.length, 1);

  const allowed = auditSkills(skills, ['misc/sketchy']);
  assert.equal(allowed.errors.length, 0);
  assert.equal(allowed.active.length, 0);
  assert.equal(allowed.allowed.length, 3);

  const partial = auditSkills(skills, ['misc/sketchy:curl-pipe-sh']);
  assert.equal(partial.errors.length, 1);
  assert.equal(partial.errors[0].rule, 'prompt-injection');
});
