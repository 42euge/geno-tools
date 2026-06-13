import fs from 'node:fs';
import path from 'node:path';
import { parseYaml, serializeYaml, YamlError } from './yaml.js';

export const MANIFEST_FILE = 'geno-image.yaml';
export const KNOWN_TARGETS = ['claude', 'codex', 'cursor', 'opencode', 'gemini', 'generic'];

const SKILL_ID_RE = /^[A-Za-z0-9_.-]+(\/[A-Za-z0-9_.-]+)*$/;

export function defaultManifest() {
  return {
    name: 'geno-strict-env',
    version: '1.0.0',
    layers: [],
    install: [],
    exclude: [],
    targets: [...KNOWN_TARGETS],
    audit: { allow: [] },
  };
}

function asStringList(value, key, errors) {
  if (value === null || value === undefined) return [];
  if (!Array.isArray(value)) {
    errors.push(`"${key}" must be a list`);
    return [];
  }
  const out = [];
  for (const v of value) {
    if (typeof v !== 'string' || !v.trim()) {
      errors.push(`"${key}" contains a non-string entry: ${JSON.stringify(v)}`);
      continue;
    }
    out.push(v.trim());
  }
  return out;
}

// Loads and validates geno-image.yaml.
// Returns { manifest, errors, warnings }; manifest is null when unreadable.
export function loadManifest(manifestPath) {
  const errors = [];
  const warnings = [];
  const fileName = path.basename(manifestPath);

  if (!fs.existsSync(manifestPath)) {
    return { manifest: null, errors: [`No ${fileName} found. Run \`geno init\` to create one.`], warnings };
  }

  let raw;
  try {
    raw = parseYaml(fs.readFileSync(manifestPath, 'utf8'));
  } catch (e) {
    if (e instanceof YamlError) {
      return { manifest: null, errors: [`${fileName}: ${e.message}`], warnings };
    }
    throw e;
  }

  const manifest = defaultManifest();

  for (const key of Object.keys(raw)) {
    if (!['name', 'version', 'layers', 'install', 'exclude', 'targets', 'audit'].includes(key)) {
      warnings.push(`Unknown manifest key "${key}" ignored`);
    }
  }

  if (typeof raw.name === 'string' && raw.name.trim()) manifest.name = raw.name.trim();
  else warnings.push(`No "name" set, defaulting to "${manifest.name}"`);
  if (typeof raw.version === 'string' && raw.version.trim()) manifest.version = raw.version.trim();
  else if (typeof raw.version === 'number') manifest.version = String(raw.version);
  else warnings.push(`No "version" set, defaulting to "${manifest.version}"`);

  if (!('layers' in raw)) warnings.push('Manifest has no "layers" key — nothing to bake from');
  manifest.layers = asStringList(raw.layers, 'layers', errors);

  if (!('install' in raw)) warnings.push('Manifest has no "install" key — nothing will be installed');
  const install = asStringList(raw.install, 'install', errors);
  const seen = new Set();
  manifest.install = [];
  for (const id of install) {
    if (!SKILL_ID_RE.test(id)) {
      errors.push(`Invalid install entry "${id}" (expected "name" or "category/name")`);
      continue;
    }
    if (seen.has(id)) {
      warnings.push(`Duplicate install entry "${id}" ignored`);
      continue;
    }
    seen.add(id);
    manifest.install.push(id);
  }

  manifest.exclude = asStringList(raw.exclude, 'exclude', errors);

  if ('targets' in raw && raw.targets !== null) {
    const targets = asStringList(raw.targets, 'targets', errors);
    for (const t of targets) {
      if (!KNOWN_TARGETS.includes(t)) {
        errors.push(`Unknown target "${t}" (known: ${KNOWN_TARGETS.join(', ')})`);
      }
    }
    manifest.targets = targets.filter((t) => KNOWN_TARGETS.includes(t));
    if (manifest.targets.length === 0 && targets.length > 0) {
      errors.push('"targets" has no valid entries');
    }
  }

  if ('audit' in raw && raw.audit !== null) {
    if (typeof raw.audit !== 'object' || Array.isArray(raw.audit)) {
      errors.push('"audit" must be a map (e.g. audit: / allow: [...])');
    } else {
      manifest.audit.allow = asStringList(raw.audit.allow, 'audit.allow', errors);
    }
  }

  return { manifest, errors, warnings };
}

export function saveManifest(manifestPath, manifest) {
  const doc = {
    name: manifest.name,
    version: manifest.version,
    layers: manifest.layers,
    install: manifest.install,
    exclude: manifest.exclude,
  };
  // Omit targets when it's the full default set; omit audit when no allowlist.
  if (manifest.targets && manifest.targets.length && manifest.targets.length !== KNOWN_TARGETS.length) {
    doc.targets = manifest.targets;
  }
  if (manifest.audit && manifest.audit.allow && manifest.audit.allow.length) {
    doc.audit = { allow: manifest.audit.allow };
  }
  fs.writeFileSync(manifestPath, serializeYaml(doc));
}

// An exclude entry matches either the full install id ("core/geno-tools")
// or, when it has no slash, the skill's basename ("geno-tools").
export function isExcluded(skillId, exclude) {
  const base = skillId.split('/').pop();
  return exclude.some((e) => e === skillId || (!e.includes('/') && e === base));
}
