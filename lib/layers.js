import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { parseFrontmatter, YamlError } from './yaml.js';

const MAX_SKILL_DEPTH = 4;

export function isRemoteSource(source) {
  return source.startsWith('http://') || source.startsWith('https://') || source.startsWith('git@');
}

export function layerNameFromSource(source) {
  return source.replace(/\/+$/, '').split('/').pop().replace(/\.git$/, '');
}

function git(args, cwd) {
  return execFileSync('git', args, {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
}

export function cloneOrUpdate(url, cacheDir) {
  const targetDir = path.join(cacheDir, layerNameFromSource(url));
  if (fs.existsSync(targetDir)) {
    git(['-C', targetDir, 'pull', '--ff-only'], undefined);
  } else {
    fs.mkdirSync(cacheDir, { recursive: true });
    git(['clone', '--depth', '1', url, targetDir], undefined);
  }
  return targetDir;
}

function gitCommit(dir) {
  try {
    return git(['-C', dir, 'rev-parse', 'HEAD'], undefined);
  } catch {
    return null;
  }
}

// Resolves manifest layer sources to local directories.
// Remote sources are cloned/updated into cacheDir; failures are collected,
// never swallowed. Returns { layers: [{source, type, name, path, commit}], errors }.
export function resolveLayers(sources, { cwd = process.cwd(), cacheDir } = {}) {
  const layers = [];
  const errors = [];
  const seen = new Set();
  for (const rawSource of sources) {
    const source = rawSource.replace(/\/+$/, '');
    if (seen.has(source)) continue;
    seen.add(source);
    if (isRemoteSource(source)) {
      try {
        const dir = cloneOrUpdate(source, cacheDir);
        layers.push({ source, type: 'git', name: layerNameFromSource(source), path: dir, commit: gitCommit(dir) });
      } catch (e) {
        const detail = (e.stderr || e.message || '').toString().trim().split('\n').pop();
        errors.push(`Failed to fetch layer ${source}: ${detail}`);
      }
    } else {
      const dir = path.resolve(cwd, source);
      if (!fs.existsSync(dir)) {
        errors.push(`Local layer missing: ${source} (resolved to ${dir})`);
        continue;
      }
      layers.push({ source, type: 'local', name: path.basename(dir), path: dir, commit: null });
    }
  }
  return { layers, errors };
}

// Lists skill ids ("category/name" or "name") under <layerPath>/skills.
// A skill is any directory containing a SKILL.md.
export function walkSkills(layerPath) {
  const skillsDir = path.join(layerPath, 'skills');
  if (!fs.existsSync(skillsDir)) return [];
  const found = [];
  const walk = (dir, prefix, depth) => {
    const entries = fs.readdirSync(dir);
    if (entries.includes('SKILL.md')) {
      found.push(prefix);
      return;
    }
    if (depth >= MAX_SKILL_DEPTH) return;
    for (const e of entries) {
      const f = path.join(dir, e);
      if (fs.statSync(f).isDirectory()) {
        walk(f, prefix ? `${prefix}/${e}` : e, depth + 1);
      }
    }
  };
  walk(skillsDir, '', 0);
  return found.sort();
}

// Finds a skill across resolved layers. Later layers win (Yocto-style override).
export function findSkill(layers, skillId) {
  for (let i = layers.length - 1; i >= 0; i--) {
    const skillPath = path.join(layers[i].path, 'skills', skillId);
    if (fs.existsSync(path.join(skillPath, 'SKILL.md'))) {
      return { layer: layers[i], path: skillPath };
    }
  }
  return null;
}

// Reads layer.json metadata. Returns { name, ecosystem, error }.
export function readLayerMeta(layerPath) {
  const metaPath = path.join(layerPath, 'layer.json');
  if (!fs.existsSync(metaPath)) return { name: null, ecosystem: null, error: null };
  try {
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    return { name: meta.name || null, ecosystem: meta.ecosystem || null, error: null };
  } catch (e) {
    return { name: null, ecosystem: null, error: `Invalid layer.json in ${layerPath}: ${e.message}` };
  }
}

// Reads SKILL.md frontmatter for a skill directory.
// Returns { name, description, allowedTools, error }.
export function readSkillMeta(skillDir) {
  const skillFile = path.join(skillDir, 'SKILL.md');
  const empty = { name: null, description: null, allowedTools: null, error: null };
  if (!fs.existsSync(skillFile)) return { ...empty, error: 'No SKILL.md' };
  try {
    const fm = parseFrontmatter(fs.readFileSync(skillFile, 'utf8'));
    if (!fm) return { ...empty, error: 'No frontmatter in SKILL.md' };
    return {
      name: typeof fm.name === 'string' ? fm.name : null,
      description: typeof fm.description === 'string' ? fm.description.replace(/\s+/g, ' ').trim() : null,
      allowedTools: typeof fm['allowed-tools'] === 'string' ? fm['allowed-tools'] : null,
      error: null,
    };
  } catch (e) {
    if (e instanceof YamlError) return { ...empty, error: `Frontmatter: ${e.message}` };
    throw e;
  }
}

export function groupBy(items, keyFn) {
  const groups = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return groups;
}
