import fs from 'node:fs';
import path from 'node:path';
import { readSkillMeta } from './layers.js';

// Static compliance rules applied to every file of every skill entering a bake
// (TENETS #3: auditing gates every ingestion path). Regex-only, local-only.
// "error" findings block the bake unless allowlisted; "warn" findings inform.
export const RULES = [
  {
    id: 'curl-pipe-sh',
    severity: 'error',
    describe: 'Pipes a remote download straight into a shell',
    re: /\b(curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(ba|z|da)?sh\b/,
  },
  {
    id: 'prompt-injection',
    severity: 'error',
    describe: 'Instruction that subverts the agent or hides actions from the user',
    re: /ignore\s+(all\s+)?(previous|prior|above)\s+instructions|do\s+not\s+(tell|inform|alert)\s+the\s+user|without\s+the\s+user(?:'s)?\s+(knowledge|knowing|consent)/i,
  },
  {
    id: 'credential-access',
    severity: 'error',
    describe: 'Touches credential stores (SSH keys, cloud credentials, keychain)',
    re: /~\/\.ssh\/(?:id_|.*key)|~\/\.aws\/credentials|security\s+find-generic-password|\/etc\/shadow/,
  },
  {
    id: 'destructive',
    severity: 'error',
    describe: 'Destructive filesystem command',
    re: /rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+(\/|~)(\s|$|")|chmod\s+(-R\s+)?777\s+\//,
  },
  {
    id: 'exfil',
    severity: 'warn',
    describe: 'Possible data exfiltration pattern',
    re: /base64\b[^\n]*\|\s*(curl|wget|nc)\b|\bnc\s+-l\b/,
  },
  {
    id: 'system-write',
    severity: 'warn',
    describe: 'Writes to system paths or escalates with sudo',
    re: /(?:>>?|\btee\b)\s+\/(?:etc|usr|bin|sbin)\/|sudo\s+(rm|mv|cp|tee|sh|bash|chmod|chown)\b/,
  },
];

const TEXT_EXTENSIONS = new Set([
  '.md', '.txt', '.json', '.yaml', '.yml', '.js', '.mjs', '.cjs', '.ts',
  '.py', '.sh', '.bash', '.zsh', '.toml', '.cfg', '.ini', '.html', '.css',
]);

function isTextFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (TEXT_EXTENSIONS.has(ext)) return true;
  if (ext) return false;
  // Extensionless: sniff for NUL bytes.
  try {
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(512);
    const n = fs.readSync(fd, buf, 0, 512, 0);
    fs.closeSync(fd);
    return !buf.subarray(0, n).includes(0);
  } catch {
    return false;
  }
}

function listFiles(dir) {
  const files = [];
  const walk = (d, rel) => {
    for (const e of fs.readdirSync(d).sort()) {
      const f = path.join(d, e);
      const r = rel ? `${rel}/${e}` : e;
      const st = fs.lstatSync(f);
      if (st.isDirectory()) walk(f, r);
      else if (st.isFile()) files.push({ abs: f, rel: r });
    }
  };
  walk(dir, '');
  return files;
}

// Scans one skill directory. Returns findings:
// [{ rule, severity, skill, file, line, excerpt, describe }]
export function auditSkillDir(skillDir, skillId) {
  const findings = [];
  for (const { abs, rel } of listFiles(skillDir)) {
    if (!isTextFile(abs)) continue;
    const lines = fs.readFileSync(abs, 'utf8').split('\n');
    for (const rule of RULES) {
      for (let n = 0; n < lines.length; n++) {
        const match = lines[n].match(rule.re);
        if (match) {
          findings.push({
            rule: rule.id,
            severity: rule.severity,
            skill: skillId,
            file: rel,
            line: n + 1,
            excerpt: lines[n].trim().slice(0, 120),
            describe: rule.describe,
          });
        }
      }
    }
  }

  // Frontmatter-level rule: overly broad or missing tool permissions.
  const meta = readSkillMeta(skillDir);
  if (!meta.error) {
    if (meta.allowedTools === null) {
      findings.push({
        rule: 'broad-tools', severity: 'warn', skill: skillId,
        file: 'SKILL.md', line: 1,
        excerpt: 'frontmatter has no allowed-tools',
        describe: 'No allowed-tools declared — skill runs with unrestricted tools',
      });
    } else if (/Bash\(\*\)|^\*$/.test(meta.allowedTools.trim())) {
      findings.push({
        rule: 'broad-tools', severity: 'warn', skill: skillId,
        file: 'SKILL.md', line: 1,
        excerpt: `allowed-tools: ${meta.allowedTools.slice(0, 100)}`,
        describe: 'allowed-tools grants unrestricted Bash',
      });
    }
  }

  return findings;
}

// Allowlist entries: "category/skill" (all rules) or "category/skill:rule".
// A bare basename ("geno-tools") also matches, mirroring exclude semantics.
export function isFindingAllowed(finding, allow) {
  const base = finding.skill.split('/').pop();
  return allow.some((entry) => {
    const [skillPart, rulePart] = entry.includes(':') ? entry.split(':') : [entry, null];
    const skillMatches = skillPart === finding.skill || (!skillPart.includes('/') && skillPart === base);
    return skillMatches && (rulePart === null || rulePart === finding.rule);
  });
}

// Audits a set of planned skills, partitioning by allowlist.
// skills: [{ id, path }]. Returns { active, allowed, errors, warns }.
export function auditSkills(skills, allow = []) {
  const active = [];
  const allowed = [];
  for (const skill of skills) {
    for (const finding of auditSkillDir(skill.path, skill.id)) {
      (isFindingAllowed(finding, allow) ? allowed : active).push(finding);
    }
  }
  return {
    active,
    allowed,
    errors: active.filter((f) => f.severity === 'error'),
    warns: active.filter((f) => f.severity === 'warn'),
  };
}
