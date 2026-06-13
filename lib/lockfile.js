import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export const LOCK_FILE = 'geno-image.lock';

// Deterministic JSON: sorted keys, no timestamps, trailing newline.
// Two bakes of identical inputs must produce byte-identical lockfiles.
export function stableStringify(value, indent = 2) {
  const sort = (v) => {
    if (Array.isArray(v)) return v.map(sort);
    if (v && typeof v === 'object') {
      return Object.fromEntries(Object.keys(v).sort().map((k) => [k, sort(v[k])]));
    }
    return v;
  };
  return JSON.stringify(sort(value), null, indent);
}

function sha256(input) {
  return 'sha256:' + crypto.createHash('sha256').update(input).digest('hex');
}

// Content hash of a skill directory: sha256 over sorted relpath\0bytes\0 pairs.
export function hashSkillDir(dir) {
  const files = [];
  const walk = (d, rel) => {
    for (const e of fs.readdirSync(d).sort()) {
      const f = path.join(d, e);
      const r = rel ? `${rel}/${e}` : e;
      const st = fs.lstatSync(f);
      if (st.isDirectory()) walk(f, r);
      else if (st.isFile()) files.push([r, f]);
    }
  };
  walk(dir, '');
  const h = crypto.createHash('sha256');
  for (const [rel, f] of files) {
    h.update(rel);
    h.update('\0');
    h.update(fs.readFileSync(f));
    h.update('\0');
  }
  return 'sha256:' + h.digest('hex');
}

// skills: [{ id, layer: {name}, path }]
export function computeLock(manifest, layers, skills) {
  return {
    lockfileVersion: 1,
    name: manifest.name,
    version: manifest.version,
    manifestHash: sha256(stableStringify({
      layers: manifest.layers,
      install: manifest.install,
      exclude: manifest.exclude,
      targets: manifest.targets,
    }, 0)),
    layers: layers.map((l) => ({
      source: l.source,
      type: l.type,
      name: l.name,
      ...(l.commit ? { commit: l.commit } : {}),
    })),
    skills: skills
      .map((s) => ({ id: s.id, layer: s.layer.name, hash: hashSkillDir(s.path) }))
      .sort((a, b) => a.id.localeCompare(b.id)),
  };
}

export function readLock(lockPath) {
  try {
    return JSON.parse(fs.readFileSync(lockPath, 'utf8'));
  } catch {
    return null;
  }
}

export function writeLock(lockPath, lock) {
  fs.writeFileSync(lockPath, stableStringify(lock) + '\n');
}

// Compares a previous lock against a freshly computed one.
// Returns { drifted, manifestChanged, changes: [{id, kind: changed|added|removed}] }.
export function compareLock(prev, next) {
  const changes = [];
  const prevSkills = new Map((prev.skills || []).map((s) => [s.id, s.hash]));
  const nextSkills = new Map((next.skills || []).map((s) => [s.id, s.hash]));
  for (const [id, hash] of nextSkills) {
    if (!prevSkills.has(id)) changes.push({ id, kind: 'added' });
    else if (prevSkills.get(id) !== hash) changes.push({ id, kind: 'changed' });
  }
  for (const id of prevSkills.keys()) {
    if (!nextSkills.has(id)) changes.push({ id, kind: 'removed' });
  }
  const manifestChanged = prev.manifestHash !== next.manifestHash;
  return { drifted: changes.length > 0 || manifestChanged, manifestChanged, changes };
}
