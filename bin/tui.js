// The interactive environment builder — the primary geno experience.
//
// Flow: REPOS → MODE → SKILLS (manual mode) → TARGETS → bake.
// Extras: drift banner on launch, inline audit glyphs with an `a` detail view
// and interactive allowlisting, `/` type-to-filter, opt-in GitHub discovery.

import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { colors, LOGO } from '../lib/log.js';
import {
  loadManifest, saveManifest, defaultManifest, MANIFEST_FILE, KNOWN_TARGETS,
} from '../lib/manifest.js';
import {
  walkSkills, readLayerMeta, readSkillMeta, cloneOrUpdate, isRemoteSource, layerNameFromSource,
} from '../lib/layers.js';
import { auditSkillDir, isFindingAllowed } from '../lib/audit.js';
import { checkDrift } from '../lib/bake.js';
import { runBakeWithOutput } from '../lib/run-bake.js';
import { TARGET_INFO } from '../lib/adapters.js';

const GITHUB_USER = '42euge';

export async function startInteractiveTui() {
  const cwd = process.cwd();
  const manifestPath = path.join(cwd, MANIFEST_FILE);
  const cacheDir = path.join(cwd, '.geno-bake-cache', 'layers');

  const { manifest: loaded, errors: manifestErrors, warnings: manifestWarnings } = loadManifest(manifestPath);
  if (manifestErrors.length && loaded === null) {
    for (const e of manifestErrors) console.log(`${colors.red}✗ ${e}${colors.reset}`);
    process.exit(1);
  }
  const manifest = loaded || defaultManifest();
  if (manifestErrors.length) {
    for (const e of manifestErrors) console.log(`${colors.red}✗ ${e}${colors.reset}`);
    console.log(`${colors.dim}Fix ${MANIFEST_FILE} and re-run geno.${colors.reset}`);
    process.exit(1);
  }

  // ---- Repo (layer) catalog -------------------------------------------------

  const repoEntries = []; // { source, name, remote, path|null, ecosystem, skills|null }

  function addRepo(source) {
    const normalized = source.replace(/\/+$/, '');
    if (repoEntries.some((r) => r.source === normalized)) return null;
    const entry = {
      source: normalized,
      name: layerNameFromSource(normalized),
      remote: isRemoteSource(normalized),
      path: null,
      ecosystem: null,
      skills: null,
    };
    if (entry.remote) {
      const cached = path.join(cacheDir, entry.name);
      if (fs.existsSync(cached)) entry.path = cached;
    } else {
      const dir = path.resolve(cwd, normalized);
      if (fs.existsSync(dir)) entry.path = dir;
    }
    if (entry.path) {
      const meta = readLayerMeta(entry.path);
      entry.ecosystem = meta.ecosystem;
      entry.skills = walkSkills(entry.path);
    }
    if (!entry.ecosystem) {
      entry.ecosystem = entry.remote
        ? (entry.source.includes(GITHUB_USER) ? `geno-ecosystem (GitHub: ${GITHUB_USER})` : 'Remote Skills (Uncategorized)')
        : 'Local Skills (Uncategorized)';
    }
    repoEntries.push(entry);
    return entry;
  }

  for (const source of manifest.layers) addRepo(source);

  // Auto-discover local layers under ./layers
  const layersDir = path.join(cwd, 'layers');
  if (fs.existsSync(layersDir)) {
    for (const d of fs.readdirSync(layersDir).sort()) {
      const p = path.join(layersDir, d);
      if (fs.statSync(p).isDirectory() && fs.existsSync(path.join(p, 'skills'))) {
        addRepo(`./layers/${d}`);
      }
    }
  }

  const selectedRepos = new Set(
    manifest.layers.length
      ? manifest.layers.map((s) => s.replace(/\/+$/, ''))
      : repoEntries.filter((r) => !r.remote).map((r) => r.source),
  );

  // ---- Drift banner ---------------------------------------------------------

  let drift = null;
  try { drift = checkDrift({ cwd }); } catch { /* banner only — never block launch */ }

  // ---- TUI state ------------------------------------------------------------

  let step = 'REPOS'; // REPOS | MODE | SKILLS | TARGETS | AUDIT
  let cursor = 0;
  let mode = 'ALL';
  const selectedSkills = new Set(manifest.install);
  const selectedTargets = new Set(manifest.targets.length ? manifest.targets : KNOWN_TARGETS);
  const allowlist = new Set(manifest.audit.allow);
  let filter = '';
  let filterMode = false;
  let auditDetail = null; // { id, findings }
  let statusMsg = '';
  let discovering = false;
  let discovered = false;
  let skillItems = []; // { id, path, repoName, meta, findings }

  const auditCache = new Map(); // skill path -> raw findings
  const findingsFor = (item) => {
    if (!auditCache.has(item.path)) auditCache.set(item.path, auditSkillDir(item.path, item.id));
    return auditCache.get(item.path);
  };
  const activeFindings = (item) =>
    findingsFor(item).filter((f) => !isFindingAllowed(f, [...allowlist]));

  const termWidth = () => process.stdout.columns || 100;

  // ---- Raw-mode plumbing ----------------------------------------------------

  const rawOn = () => {
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.setEncoding('utf8');
    process.stdout.write('\x1B[?25l');
  };
  const rawOff = () => {
    process.stdout.write('\x1B[?25h');
    process.stdin.setRawMode(false);
    process.stdin.pause();
  };

  // ---- Row models (one actionable list per step) ----------------------------

  function rows() {
    if (step === 'REPOS') {
      return [
        ...repoEntries.map((entry) => ({ kind: 'repo', entry })),
        { kind: 'discover' },
        { kind: 'next' },
      ];
    }
    if (step === 'MODE') {
      return [{ kind: 'mode', value: 'ALL' }, { kind: 'mode', value: 'MANUAL' }];
    }
    if (step === 'SKILLS') {
      const visible = filter
        ? skillItems.filter((s) => s.id.toLowerCase().includes(filter.toLowerCase()))
        : skillItems;
      return [...visible.map((item) => ({ kind: 'skill', item })), { kind: 'next' }];
    }
    if (step === 'TARGETS') {
      return [...KNOWN_TARGETS.map((target) => ({ kind: 'target', target })), { kind: 'bake' }];
    }
    if (step === 'AUDIT') {
      const r = [];
      if (auditDetail.findings.length) r.push({ kind: 'allow' });
      r.push({ kind: 'back' });
      return r;
    }
    return [];
  }

  // ---- Rendering ------------------------------------------------------------

  function hl(line, hovered) {
    return hovered ? `${colors.bold}${line}${colors.reset}` : line;
  }

  function auditGlyph(item) {
    const findings = activeFindings(item);
    const errors = findings.filter((f) => f.severity === 'error').length;
    const warns = findings.filter((f) => f.severity === 'warn').length;
    if (errors) return `${colors.red}✗${errors}${colors.reset}`;
    if (warns) return `${colors.yellow}⚠${warns}${colors.reset}`;
    return `${colors.green}✓${colors.reset}`;
  }

  function render() {
    readline.cursorTo(process.stdout, 0, 0);
    readline.clearScreenDown(process.stdout);
    console.log(`${LOGO} ${colors.dim}- Interactive Environment Builder${colors.reset}\n`);

    if (drift && drift.drifted && step === 'REPOS') {
      const names = drift.changes.slice(0, 3).map((c) => c.id);
      const more = drift.changes.length - names.length;
      const detail = drift.changes.length
        ? `${names.join(', ')}${more > 0 ? ` +${more} more` : ''}`
        : 'manifest changed';
      console.log(`${colors.yellow}⚠ Environment drifted since last bake (${detail}) — re-bake to sync.${colors.reset}\n`);
    }
    for (const w of manifestWarnings) {
      console.log(`${colors.dim}⚠ ${w}${colors.reset}`);
    }

    const rowList = rows();
    const hover = (row) => rowList.indexOf(row) === cursor;

    if (step === 'REPOS') {
      console.log(`${colors.bold}Step 1: Select Skill Layers${colors.reset}`);
      console.log(`${colors.dim}TAB/↑↓ navigate · ENTER/SPACE toggle · ESC quit${colors.reset}`);

      const groups = new Map();
      for (const entry of repoEntries) {
        if (!groups.has(entry.ecosystem)) groups.set(entry.ecosystem, []);
        groups.get(entry.ecosystem).push(entry);
      }
      for (const [eco, entries] of groups) {
        console.log(`\n  ${colors.blue}${colors.bold}🏢 ${eco}${colors.reset}`);
        for (const entry of entries) {
          const row = rowList.find((r) => r.kind === 'repo' && r.entry === entry);
          const checkbox = selectedRepos.has(entry.source) ? `${colors.green}[✓]${colors.reset}` : '[ ]';
          const prefix = hover(row) ? `${colors.cyan}❯${colors.reset}` : ' ';
          const count = entry.skills === null
            ? `${colors.dim}(remote, not fetched)${colors.reset}`
            : `${colors.dim}(${entry.skills.length} skill${entry.skills.length === 1 ? '' : 's'})${colors.reset}`;
          console.log(hl(`  ${prefix} ${checkbox} ${entry.name} ${count}`, hover(row)));
        }
      }

      console.log('');
      const discoverRow = rowList.find((r) => r.kind === 'discover');
      const discoverLabel = discovering
        ? `[ 🔍 Scanning GitHub (${GITHUB_USER})... ]`
        : discovered ? '[ 🔍 Re-scan GitHub for layers ]' : '[ 🔍 Discover remote layers (GitHub) ]';
      console.log(hl(`${hover(discoverRow) ? `${colors.cyan}❯${colors.reset}` : ' '} ${discoverLabel}`, hover(discoverRow)));
      const nextRow = rowList.find((r) => r.kind === 'next');
      console.log(hl(`${hover(nextRow) ? `${colors.cyan}❯${colors.reset}` : ' '} ${colors.green}[ Next Step → ]${colors.reset}`, hover(nextRow)));

    } else if (step === 'MODE') {
      console.log(`${colors.bold}Step 2: Installation Mode${colors.reset}`);
      console.log(`${colors.dim}TAB/↑↓ navigate · ENTER select${colors.reset}\n`);
      const labels = { ALL: 'Install ALL skills from selected layers', MANUAL: 'Manually select specific skills' };
      for (const row of rowList) {
        const radio = mode === row.value ? `${colors.green}(•)${colors.reset}` : '( )';
        const prefix = hover(row) ? `${colors.cyan}❯${colors.reset}` : ' ';
        console.log(hl(`  ${prefix} ${radio} ${labels[row.value]}`, hover(row)));
      }

    } else if (step === 'SKILLS') {
      console.log(`${colors.bold}Step 3: Select Skills${colors.reset}`);
      console.log(`${colors.dim}SPACE toggle · a audit details · / filter · ENTER on [Next] to continue${colors.reset}`);
      if (filterMode || filter) {
        console.log(`  ${colors.cyan}/${filter}${filterMode ? '▌' : ''}${colors.reset}`);
      }

      let lastRepo = null;
      let shown = 0;
      for (const row of rowList) {
        if (row.kind !== 'skill') continue;
        const { item } = row;
        if (item.repoName !== lastRepo) {
          console.log(`\n  ${colors.blue}${colors.bold}📁 ${item.repoName}${colors.reset}`);
          lastRepo = item.repoName;
        }
        const checkbox = selectedSkills.has(item.id) ? `${colors.green}[✓]${colors.reset}` : '[ ]';
        const prefix = hover(row) ? `${colors.cyan}❯${colors.reset}` : ' ';
        const head = `    ${prefix} ${checkbox} ${item.id} ${auditGlyph(item)}`;
        const headLen = 9 + item.id.length + 3;
        const room = termWidth() - headLen - 4;
        const desc = item.meta.description && room > 12
          ? ` ${colors.dim}— ${item.meta.description.slice(0, room)}${colors.reset}`
          : '';
        console.log(hl(`${head}${desc}`, hover(row)));
        shown++;
      }
      if (shown === 0) console.log(`\n  ${colors.dim}(no skills match "${filter}")${colors.reset}`);

      console.log('');
      const nextRow = rowList.find((r) => r.kind === 'next');
      console.log(hl(`${hover(nextRow) ? `${colors.cyan}❯${colors.reset}` : ' '} ${colors.green}[ Next: Choose Targets → ]${colors.reset}`, hover(nextRow)));

    } else if (step === 'TARGETS') {
      console.log(`${colors.bold}Step 4: Agent Targets${colors.reset}`);
      console.log(`${colors.dim}The bake emits an adapter manifest for each selected agent.${colors.reset}\n`);
      for (const row of rowList) {
        if (row.kind !== 'target') continue;
        const info = TARGET_INFO[row.target];
        const checkbox = selectedTargets.has(row.target) ? `${colors.green}[✓]${colors.reset}` : '[ ]';
        const prefix = hover(row) ? `${colors.cyan}❯${colors.reset}` : ' ';
        console.log(hl(`  ${prefix} ${checkbox} ${info.label} ${colors.dim}(${row.target})${colors.reset}`, hover(row)));
      }
      console.log('');
      const bakeRow = rowList.find((r) => r.kind === 'bake');
      console.log(hl(`${hover(bakeRow) ? `${colors.cyan}❯${colors.reset}` : ' '} ${colors.green}${colors.bold}[ Save & Bake Environment ]${colors.reset}`, hover(bakeRow)));

    } else if (step === 'AUDIT') {
      console.log(`${colors.bold}Audit: ${auditDetail.id}${colors.reset}\n`);
      if (auditDetail.findings.length === 0) {
        console.log(`  ${colors.green}✓ No findings — this skill is clean.${colors.reset}`);
      } else {
        for (const f of auditDetail.findings) {
          const sev = f.severity === 'error' ? `${colors.red}✗ ${f.rule}` : `${colors.yellow}⚠ ${f.rule}`;
          console.log(`  ${sev}${colors.reset} ${colors.dim}${f.file}:${f.line}${colors.reset}`);
          console.log(`      ${colors.dim}${f.describe}${colors.reset}`);
          console.log(`      ${f.excerpt.slice(0, termWidth() - 8)}`);
        }
        console.log(`\n  ${colors.dim}Error findings block the bake unless allowlisted in the manifest.${colors.reset}`);
      }
      console.log('');
      for (const row of rowList) {
        const label = row.kind === 'allow'
          ? `[ Allowlist ${auditDetail.id} ]`
          : '[ ← Back ]';
        console.log(hl(`${hover(row) ? `${colors.cyan}❯${colors.reset}` : ' '} ${label}`, hover(row)));
      }
    }

    if (statusMsg) console.log(`\n${colors.dim}${statusMsg}${colors.reset}`);
  }

  // ---- Step transitions -----------------------------------------------------

  function materializeRepo(entry) {
    if (entry.path && entry.skills !== null) return;
    entry.path = cloneOrUpdate(entry.source, cacheDir);
    const meta = readLayerMeta(entry.path);
    if (meta.ecosystem) entry.ecosystem = meta.ecosystem;
    entry.skills = walkSkills(entry.path);
  }

  function materializeSelected() {
    const chosen = repoEntries.filter((r) => selectedRepos.has(r.source));
    const failed = [];
    const remote = chosen.filter((r) => r.remote && (!r.path || r.skills === null));
    if (remote.length) {
      rawOff();
      console.log(`\n${colors.cyan}Fetching remote layers...${colors.reset}`);
      for (const entry of remote) {
        try {
          materializeRepo(entry);
          console.log(`  ${colors.green}✓${colors.reset} ${entry.name}`);
        } catch (e) {
          const detail = (e.stderr || e.message || '').toString().trim().split('\n').pop();
          console.log(`  ${colors.red}✗ ${entry.name}: ${detail}${colors.reset}`);
          failed.push(entry.name);
        }
      }
      rawOn();
    }
    if (failed.length) statusMsg = `Could not fetch: ${failed.join(', ')} — these layers are skipped.`;
    return chosen.filter((r) => r.path && r.skills !== null);
  }

  function buildSkillItems(chosenRepos) {
    skillItems = [];
    for (const repo of chosenRepos) {
      for (const id of repo.skills) {
        const skillPath = path.join(repo.path, 'skills', id);
        skillItems.push({ id, path: skillPath, repoName: repo.name, meta: readSkillMeta(skillPath) });
      }
    }
  }

  async function discoverGitHub() {
    if (discovering) return;
    discovering = true;
    statusMsg = '';
    render();
    try {
      const res = await fetch(`https://api.github.com/users/${GITHUB_USER}/repos?per_page=100`);
      if (!res.ok) throw new Error(`GitHub API ${res.status}`);
      const repos = await res.json();
      const candidates = repos
        .filter((r) => r.name && r.name.startsWith('geno-') && r.name !== 'geno-tools')
        .map((r) => `https://github.com/${GITHUB_USER}/${r.name}`);
      const added = [];
      for (const url of candidates) {
        const entry = addRepo(url);
        if (entry) added.push(entry);
      }
      // Best-effort ecosystem labels from each repo's layer.json (user opted in).
      await Promise.all(added.filter((e) => !e.path).map(async (entry) => {
        try {
          const parts = new URL(entry.source).pathname.split('/').filter(Boolean);
          const raw = await fetch(`https://raw.githubusercontent.com/${parts[0]}/${parts[1]}/main/layer.json`);
          if (raw.ok) {
            const meta = await raw.json();
            if (meta.ecosystem) entry.ecosystem = meta.ecosystem;
          }
        } catch { /* keep fallback label */ }
      }));
      discovered = true;
      statusMsg = `Found ${added.length} new remote layer${added.length === 1 ? '' : 's'}.`;
    } catch (e) {
      statusMsg = `GitHub discovery failed: ${e.message}`;
    }
    discovering = false;
    render();
  }

  function submitFinal() {
    rawOff();
    console.log('\n');

    manifest.layers = repoEntries.filter((r) => selectedRepos.has(r.source)).map((r) => r.source);
    manifest.install = [...selectedSkills].sort();
    manifest.targets = KNOWN_TARGETS.filter((t) => selectedTargets.has(t));
    manifest.audit.allow = [...allowlist].sort();
    saveManifest(manifestPath, manifest);
    console.log(`${colors.green}✨ Saved configuration to ${MANIFEST_FILE}${colors.reset}`);

    const result = runBakeWithOutput({ cwd });
    process.exit(result.ok ? 0 : 1);
  }

  // ---- Input ----------------------------------------------------------------

  function activate(row) {
    statusMsg = '';
    if (!row) return;

    if (step === 'REPOS') {
      if (row.kind === 'repo') {
        const { source } = row.entry;
        if (selectedRepos.has(source)) selectedRepos.delete(source);
        else selectedRepos.add(source);
      } else if (row.kind === 'discover') {
        discoverGitHub();
      } else if (row.kind === 'next') {
        if (selectedRepos.size === 0) { statusMsg = 'Select at least one layer.'; return; }
        step = 'MODE';
        cursor = 0;
      }
    } else if (step === 'MODE') {
      mode = row.value;
      const chosen = materializeSelected();
      if (chosen.length === 0) { statusMsg = 'No usable layers selected.'; step = 'REPOS'; cursor = 0; return; }
      buildSkillItems(chosen);
      if (mode === 'ALL') {
        selectedSkills.clear();
        for (const item of skillItems) selectedSkills.add(item.id);
        step = 'TARGETS';
      } else {
        step = 'SKILLS';
      }
      cursor = 0;
    } else if (step === 'SKILLS') {
      if (row.kind === 'skill') {
        if (selectedSkills.has(row.item.id)) selectedSkills.delete(row.item.id);
        else selectedSkills.add(row.item.id);
      } else if (row.kind === 'next') {
        if (selectedSkills.size === 0) { statusMsg = 'Select at least one skill.'; return; }
        step = 'TARGETS';
        cursor = 0;
      }
    } else if (step === 'TARGETS') {
      if (row.kind === 'target') {
        if (selectedTargets.has(row.target)) selectedTargets.delete(row.target);
        else selectedTargets.add(row.target);
      } else if (row.kind === 'bake') {
        if (selectedTargets.size === 0) { statusMsg = 'Select at least one target.'; return; }
        submitFinal();
        return;
      }
    } else if (step === 'AUDIT') {
      if (row.kind === 'allow') {
        allowlist.add(auditDetail.id);
        step = 'SKILLS';
      } else {
        step = 'SKILLS';
      }
      auditDetail = null;
      cursor = 0;
    }
  }

  // stdin delivers chunks, not keys — fast typing, paste, or driven input
  // arrives as multi-byte strings. Split into key events, keeping escape
  // sequences whole.
  function* tokenize(chunk) {
    let i = 0;
    while (i < chunk.length) {
      if (chunk[i] === '\x1b' && chunk[i + 1] === '[') {
        let j = i + 2;
        while (j < chunk.length && !(chunk[j] >= '@' && chunk[j] <= '~')) j++;
        yield chunk.slice(i, Math.min(j + 1, chunk.length));
        i = j + 1;
      } else {
        yield chunk[i];
        i++;
      }
    }
  }

  function onData(chunk) {
    for (const key of tokenize(chunk)) handleKey(key);
  }

  function handleKey(key) {
    if (key === '\u0003') { rawOff(); process.exit(0); } // Ctrl+C

    if (key === '\x1b') { // bare ESC
      if (filterMode || filter) { filterMode = false; filter = ''; cursor = 0; render(); return; }
      if (step === 'AUDIT') { step = 'SKILLS'; auditDetail = null; cursor = 0; render(); return; }
      rawOff(); process.exit(0);
    }

    const rowList = rows();
    const max = rowList.length - 1;

    if (key === '\t' || key === '\x1b[B') {
      cursor = cursor >= max ? 0 : cursor + 1;
      render(); return;
    }
    if (key === '\x1b[Z' || key === '\x1b[A') {
      cursor = cursor <= 0 ? max : cursor - 1;
      render(); return;
    }

    if (step === 'SKILLS' && filterMode) {
      if (key === '\r' || key === '\n') { filterMode = false; render(); return; }
      if (key === '\x7f' || key === '\b') { filter = filter.slice(0, -1); cursor = 0; render(); return; }
      if (key.length === 1 && key >= ' ' && key !== '\t') {
        filter += key;
        cursor = 0;
        render(); return;
      }
      return;
    }

    if (step === 'SKILLS' && key === '/') {
      filterMode = true;
      render(); return;
    }
    if (step === 'SKILLS' && key === 'a') {
      const row = rowList[cursor];
      if (row && row.kind === 'skill') {
        auditDetail = { id: row.item.id, findings: activeFindings(row.item) };
        step = 'AUDIT';
        cursor = 0;
      }
      render(); return;
    }

    if (key === '\r' || key === '\n' || key === ' ') {
      activate(rowList[cursor]);
      render(); return;
    }
  }

  rawOn();
  process.stdin.on('data', onData);
  render();
}
