#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { colors, LOGO } from '../lib/log.js';
import { defaultManifest, saveManifest, MANIFEST_FILE } from '../lib/manifest.js';
import { runBakeWithOutput } from '../lib/run-bake.js';

function printHelp() {
  console.log(`${LOGO} ${colors.dim}- The manifest-driven AI agent compiler${colors.reset}\n`);
  console.log(`${colors.bold}USAGE${colors.reset}`);
  console.log(`  $ geno            Launch the interactive environment builder`);
  console.log(`  $ geno bake       Compile the environment from geno-image.yaml (headless)`);
  console.log(`  $ geno init       Create a default geno-image.yaml`);
  console.log(`  $ geno help       Show this help message\n`);
}

function initManifest() {
  const manifestPath = path.join(process.cwd(), MANIFEST_FILE);
  if (fs.existsSync(manifestPath)) {
    console.log(`\n${colors.yellow}⚠️  A ${colors.bold}${MANIFEST_FILE}${colors.reset}${colors.yellow} manifest already exists in this directory.${colors.reset}\n`);
    console.log(`${colors.dim}To compile your environment, run:${colors.reset}`);
    console.log(`  ${colors.bold}geno bake${colors.reset}\n`);
    return;
  }
  const manifest = defaultManifest();
  manifest.layers = ['./layers/meta-geno-core'];
  manifest.install = ['core/geno-tools', 'core/geno-audit'];
  saveManifest(manifestPath, manifest);
  console.log(`${colors.green}✨ Created new manifest: ${colors.bold}${MANIFEST_FILE}${colors.reset}`);
  console.log(`${colors.dim}Next step: Run \`geno\` to configure interactively, or \`geno bake\` to compile.${colors.reset}`);
}

const command = process.argv[2] || 'tui';

switch (command) {
  case 'init': initManifest(); break;
  case 'bake': {
    const result = runBakeWithOutput();
    if (!result.ok) process.exit(1);
    break;
  }
  case 'help': case '--help': case '-h': printHelp(); break;
  case 'tui': (await import('./tui.js')).startInteractiveTui(); break;
  default:
    console.log(`${colors.red}Unknown command: ${command}${colors.reset}`);
    printHelp();
    process.exit(2);
}
