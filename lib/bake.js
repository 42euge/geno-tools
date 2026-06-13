import fs from 'node:fs';
import path from 'node:path';
import { loadManifest, isExcluded, MANIFEST_FILE } from './manifest.js';
import { resolveLayers, findSkill, isRemoteSource, layerNameFromSource } from './layers.js';
import { auditSkills } from './audit.js';
import { computeLock, readLock, writeLock, compareLock, LOCK_FILE } from './lockfile.js';
import { emitAdapters } from './adapters.js';

// The bake pipeline: load+validate manifest → resolve layers → plan skills →
// audit (errors fail) → copy → adapters → lockfile.
//
// onEvent receives progress events so the TUI and headless CLI can render the
// same run their own way:
//   {type:'error'|'warning', message}
//   {type:'layer', layer}                      resolved layer
//   {type:'skill', status:'installed'|'excluded'|'missing', id, layer?}
//   {type:'audit', result}                     full audit result
//   {type:'adapters', emitted}
//   {type:'lock', drift}                       drift vs previous lock, or null
//
// Returns { ok, manifest, layers, installed, missing, excluded, audit,
//           adapters, lock, drift, errors }.
export function bake({ cwd = process.cwd(), onEvent = () => {} } = {}) {
  const fail = (errors) => {
    for (const message of errors) onEvent({ type: 'error', message });
    return { ok: false, errors };
  };

  // 1. Manifest
  const manifestPath = path.join(cwd, MANIFEST_FILE);
  const { manifest, errors, warnings } = loadManifest(manifestPath);
  for (const message of warnings) onEvent({ type: 'warning', message });
  if (!manifest) return fail(errors);
  if (errors.length) return fail(errors);
  if (manifest.layers.length === 0) return fail(['Manifest declares no layers — nothing to bake from.']);
  if (manifest.install.length === 0) return fail(['Manifest installs no skills — nothing to bake.']);

  // 2. Layers
  const cacheDir = path.join(cwd, '.geno-bake-cache', 'layers');
  const { layers, errors: layerErrors } = resolveLayers(manifest.layers, { cwd, cacheDir });
  if (layerErrors.length) return fail(layerErrors);
  for (const layer of layers) onEvent({ type: 'layer', layer });

  // 3. Plan
  const planned = [];
  const excluded = [];
  const missing = [];
  for (const id of manifest.install) {
    if (isExcluded(id, manifest.exclude)) {
      excluded.push(id);
      onEvent({ type: 'skill', status: 'excluded', id });
      continue;
    }
    const hit = findSkill(layers, id);
    if (!hit) {
      missing.push(id);
      onEvent({ type: 'skill', status: 'missing', id });
      continue;
    }
    planned.push({ id, layer: hit.layer, path: hit.path });
  }

  // 4. Audit — gates every bake (TENETS #3); errors block unless allowlisted.
  const audit = auditSkills(planned, manifest.audit.allow);
  onEvent({ type: 'audit', result: audit });

  const buildDir = path.join(cwd, 'build');
  fs.rmSync(buildDir, { recursive: true, force: true });
  fs.mkdirSync(path.join(buildDir, 'skills'), { recursive: true });
  fs.writeFileSync(
    path.join(buildDir, 'audit-report.json'),
    JSON.stringify({ findings: audit.active, allowlisted: audit.allowed }, null, 2) + '\n',
  );

  const blockers = [];
  if (missing.length) {
    blockers.push(`Missing in all layers: ${missing.join(', ')}`);
  }
  if (audit.errors.length) {
    blockers.push(
      `Audit blocked ${audit.errors.length} finding(s) — see build/audit-report.json. ` +
      'Allowlist intentional ones under "audit: allow:" in the manifest.',
    );
  }
  if (blockers.length) {
    const result = fail(blockers);
    return { ...result, manifest, layers, installed: [], missing, excluded, audit };
  }

  // 5. Copy
  const installed = [];
  for (const skill of planned) {
    fs.cpSync(skill.path, path.join(buildDir, 'skills', skill.id), { recursive: true });
    installed.push(skill);
    onEvent({ type: 'skill', status: 'installed', id: skill.id, layer: skill.layer.name });
  }

  // 6. Adapters
  const installedIds = installed.map((s) => s.id);
  const adapters = emitAdapters(buildDir, manifest, installedIds, manifest.targets);
  onEvent({ type: 'adapters', emitted: adapters });

  // 7. Lockfile (+ drift report vs previous bake)
  const lockPath = path.join(cwd, LOCK_FILE);
  const lock = computeLock(manifest, layers, installed);
  const prev = readLock(lockPath);
  const drift = prev ? compareLock(prev, lock) : null;
  writeLock(lockPath, lock);
  onEvent({ type: 'lock', drift });

  return {
    ok: true, errors: [],
    manifest, layers, installed, missing, excluded, audit, adapters, lock, drift,
  };
}

// Lightweight drift check for the TUI launch banner: recomputes the lock from
// the current manifest + already-available layers (no network) and compares it
// to the committed lockfile. Returns null when there is nothing to compare.
export function checkDrift({ cwd = process.cwd() } = {}) {
  const lockPath = path.join(cwd, LOCK_FILE);
  const prev = readLock(lockPath);
  if (!prev) return null;

  const { manifest, errors } = loadManifest(path.join(cwd, MANIFEST_FILE));
  if (!manifest || errors.length) return null;

  // Resolve layers without touching the network — remote layers count only if
  // already cached (TENETS #5: local-first; a banner must never trigger a pull).
  const cacheDir = path.join(cwd, '.geno-bake-cache', 'layers');
  const layers = [];
  for (const source of manifest.layers) {
    if (isRemoteSource(source)) {
      const dir = path.join(cacheDir, layerNameFromSource(source));
      if (fs.existsSync(dir)) {
        layers.push({ source, type: 'git', name: layerNameFromSource(source), path: dir, commit: null });
      }
    } else {
      const dir = path.resolve(cwd, source);
      if (fs.existsSync(dir)) {
        layers.push({ source, type: 'local', name: path.basename(dir), path: dir, commit: null });
      }
    }
  }

  const planned = [];
  for (const id of manifest.install) {
    if (isExcluded(id, manifest.exclude)) continue;
    const hit = findSkill(layers, id);
    if (hit) planned.push({ id, layer: hit.layer, path: hit.path });
  }
  return compareLock(prev, computeLock(manifest, layers, planned));
}
