import fs from 'node:fs';
import path from 'node:path';

// One emitter per agent target (TENETS #1: agent-agnostic). Formats mirror the
// adapter manifests this repo itself ships for each agent.
export const TARGET_INFO = {
  claude:   { label: 'Claude Code',     installCmd: (p) => `/plugin install ${p}` },
  generic:  { label: 'Antigravity CLI', installCmd: (p) => `agy plugin install ${p}` },
  codex:    { label: 'Codex CLI',       installCmd: (p) => `/plugin install ${p}` },
  cursor:   { label: 'Cursor',          installCmd: (p) => `cursor plugin install ${p}` },
  opencode: { label: 'OpenCode',        installCmd: (p) => `opencode plugin add ${p}` },
  gemini:   { label: 'Gemini CLI',      installCmd: (p) => `gemini extensions install ${p}` },
};

function base(manifest) {
  return {
    name: manifest.name,
    version: manifest.version,
    description: 'Compiled strict AI environment (geno bake)',
  };
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + '\n');
}

const OPENCODE_SHIM = (skillsRel) => `import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { existsSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const pluginRoot = resolve(dirname(__filename), "..", "..");
const skillsDir = resolve(pluginRoot, ${JSON.stringify(skillsRel)});

export default async function GenoBakedPlugin({ config }) {
  if (!existsSync(skillsDir)) return;

  config.skills = config.skills || {};
  config.skills.paths = config.skills.paths || [];

  if (!config.skills.paths.includes(skillsDir)) {
    config.skills.paths.push(skillsDir);
  }
}
`;

const EMITTERS = {
  claude(buildDir, manifest) {
    const file = path.join(buildDir, '.claude-plugin', 'plugin.json');
    writeJson(file, { ...base(manifest), skills: './skills' });
    return file;
  },
  codex(buildDir, manifest) {
    const file = path.join(buildDir, '.codex-plugin', 'plugin.json');
    writeJson(file, {
      ...base(manifest),
      skills: './skills/',
      interface: {
        displayName: manifest.name,
        shortDescription: 'Compiled strict AI environment (geno bake)',
        category: 'Coding',
        capabilities: ['Read'],
      },
    });
    return file;
  },
  cursor(buildDir, manifest) {
    const file = path.join(buildDir, '.cursor-plugin', 'plugin.json');
    writeJson(file, { ...base(manifest), displayName: manifest.name, skills: './skills/' });
    return file;
  },
  opencode(buildDir, manifest) {
    const safeName = manifest.name.replace(/[^A-Za-z0-9._-]/g, '-');
    const file = path.join(buildDir, '.opencode', 'plugins', `${safeName}.js`);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, OPENCODE_SHIM('skills'));
    return file;
  },
  gemini(buildDir, manifest) {
    const file = path.join(buildDir, 'gemini-extension.json');
    writeJson(file, { ...base(manifest), contextFileName: 'GEMINI.md' });
    return file;
  },
  generic(buildDir, manifest, installedIds) {
    const file = path.join(buildDir, 'plugin.json');
    writeJson(file, { ...base(manifest), skills: './skills', installed_skills: installedIds });
    return file;
  },
};

export function emitAdapters(buildDir, manifest, installedIds, targets) {
  const emitted = [];
  for (const target of targets) {
    const emit = EMITTERS[target];
    if (!emit) continue;
    emitted.push({ target, file: emit(buildDir, manifest, installedIds) });
  }
  return emitted;
}
