import { colors, LOGO, glyphs } from './log.js';
import { bake } from './bake.js';
import { TARGET_INFO } from './adapters.js';

export function renderBakeEvent(event) {
  switch (event.type) {
    case 'warning':
      console.log(`  ${glyphs.warn} ${colors.yellow}${event.message}${colors.reset}`);
      break;
    case 'error':
      console.log(`  ${glyphs.fail} ${colors.red}${event.message}${colors.reset}`);
      break;
    case 'layer':
      console.log(`  ${colors.dim}▸ Layer ${event.layer.name} (${event.layer.type})${colors.reset}`);
      break;
    case 'skill':
      if (event.status === 'installed') {
        console.log(`  ${glyphs.ok} Installed ${colors.bold}${event.id}${colors.reset} ${colors.dim}(from ${event.layer})${colors.reset}`);
      } else if (event.status === 'excluded') {
        console.log(`  ${glyphs.skip} Skipped ${event.id} ${colors.dim}(excluded)${colors.reset}`);
      } else {
        console.log(`  ${glyphs.fail} ${colors.red}Missing ${event.id} in all layers${colors.reset}`);
      }
      break;
    case 'audit': {
      const { errors, warns, allowed } = event.result;
      if (errors.length === 0 && warns.length === 0) {
        console.log(`\n  ${glyphs.ok} Audit clean${allowed.length ? ` ${colors.dim}(${allowed.length} allowlisted)${colors.reset}` : ''}`);
      } else {
        console.log('');
        for (const f of [...errors, ...warns]) {
          const color = f.severity === 'error' ? colors.red : colors.yellow;
          console.log(`  ${f.severity === 'error' ? glyphs.fail : glyphs.warn} ${color}[${f.rule}]${colors.reset} ${f.skill} ${colors.dim}${f.file}:${f.line} — ${f.excerpt}${colors.reset}`);
        }
      }
      console.log('');
      break;
    }
    case 'lock':
      if (event.drift && event.drift.drifted) {
        const n = event.drift.changes.length;
        console.log(`  ${colors.dim}↻ Environment changed since last bake (${n} skill${n === 1 ? '' : 's'}) — lockfile updated${colors.reset}`);
      }
      break;
  }
}

// Runs the bake pipeline with terminal rendering. Shared by `geno bake` and
// the TUI's final step. Returns the bake result; does not exit the process.
export function runBakeWithOutput({ cwd = process.cwd(), banner = true } = {}) {
  if (banner) console.log(`\n${LOGO} ${colors.bold}Baking environment...${colors.reset}\n`);

  const result = bake({ cwd, onEvent: renderBakeEvent });

  if (!result.ok) {
    console.log(`\n${colors.red}❌ Bake failed.${colors.reset}\n`);
    return result;
  }

  console.log(`\n${colors.cyan}🚀 Bake complete!${colors.reset} Environment ready in ${colors.bold}./build${colors.reset}`);
  console.log(`${colors.dim}Audit report: build/audit-report.json · Lockfile: geno-image.lock${colors.reset}`);
  console.log(`${colors.dim}Install this into your agent to enforce these restrictions:${colors.reset}\n`);
  for (const { target } of result.adapters) {
    const info = TARGET_INFO[target];
    console.log(`  ${colors.bold}${info.label.padEnd(16)}${colors.reset} ${info.installCmd('./build')}`);
  }
  console.log('');
  return result;
}
