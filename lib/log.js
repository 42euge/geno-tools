export const colors = {
  reset: '\x1b[0m', green: '\x1b[32m', blue: '\x1b[34m',
  cyan: '\x1b[36m', yellow: '\x1b[33m', red: '\x1b[31m',
  bold: '\x1b[1m', dim: '\x1b[2m',
};

export const LOGO = `${colors.bold}${colors.cyan}🧬 geno-tools${colors.reset}`;

export const glyphs = {
  ok: `${colors.green}✓${colors.reset}`,
  warn: `${colors.yellow}⚠${colors.reset}`,
  fail: `${colors.red}✗${colors.reset}`,
  skip: `${colors.dim}⊘${colors.reset}`,
};
