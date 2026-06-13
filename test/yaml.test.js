import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseYaml, serializeYaml, parseFrontmatter, YamlError } from '../lib/yaml.js';

test('parses top-level scalars with and without quotes', () => {
  const doc = parseYaml('name: "geno-strict-env"\nversion: 1.0.0\nflag: true\n');
  assert.equal(doc.name, 'geno-strict-env');
  assert.equal(doc.version, '1.0.0');
  assert.equal(doc.flag, true);
});

test('only strips quotes that wrap the whole token', () => {
  const doc = parseYaml('name: say "hi" there\n');
  assert.equal(doc.name, 'say "hi" there');
});

test('parses lists of scalars', () => {
  const doc = parseYaml('install:\n  - core/geno-tools\n  - "core/geno-audit"\n');
  assert.deepEqual(doc.install, ['core/geno-tools', 'core/geno-audit']);
});

test('parses inline flow lists including empty', () => {
  const doc = parseYaml('exclude: []\ntargets: [claude, generic]\n');
  assert.deepEqual(doc.exclude, []);
  assert.deepEqual(doc.targets, ['claude', 'generic']);
});

test('parses one level of nested maps with nested lists', () => {
  const doc = parseYaml('audit:\n  allow:\n    - misc/x:curl-pipe-sh\n  mode: strict\n');
  assert.deepEqual(doc.audit, { allow: ['misc/x:curl-pipe-sh'], mode: 'strict' });
});

test('parses folded block scalars', () => {
  const doc = parseYaml('description: >-\n  line one\n  line two\n');
  assert.equal(doc.description, 'line one line two');
});

test('strips comments outside quotes only', () => {
  const doc = parseYaml('name: hello # comment\nurl: "http://x/#frag"\n');
  assert.equal(doc.name, 'hello');
  assert.equal(doc.url, 'http://x/#frag');
});

test('errors loudly instead of misparsing', () => {
  assert.throws(() => parseYaml('a:\n  b:\n    c:\n      d: 1\n'), YamlError);
  assert.throws(() => parseYaml('name: "unterminated\n'), YamlError);
  assert.throws(() => parseYaml('items:\n  - key: value\n'), YamlError);
  assert.throws(() => parseYaml('ref: &anchor x\n'), YamlError);
  assert.throws(() => parseYaml('\tname: tabbed\n'), YamlError);
});

test('missing keys are absent, not silently defaulted', () => {
  const doc = parseYaml('name: x\n');
  assert.equal('install' in doc, false);
});

test('serialize → parse round-trips a manifest', () => {
  const manifest = {
    name: 'env',
    version: '1.0.0',
    layers: ['./layers/meta-geno-core'],
    install: ['core/geno-tools'],
    exclude: [],
    audit: { allow: ['misc/x:curl-pipe-sh'] },
  };
  assert.deepEqual(parseYaml(serializeYaml(manifest)), manifest);
});

test('parseFrontmatter extracts the leading block only', () => {
  const fm = parseFrontmatter('---\nname: x\ndescription: >-\n  multi\n  line\n---\n\n# Body\n\n---\nnot frontmatter\n');
  assert.equal(fm.name, 'x');
  assert.equal(fm.description, 'multi line');
  assert.equal(parseFrontmatter('# No frontmatter\n'), null);
});
