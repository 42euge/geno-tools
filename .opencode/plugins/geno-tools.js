import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { existsSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const pluginRoot = resolve(dirname(__filename), "..", "..");
const skillsDir = resolve(pluginRoot, "skills");

export default async function GenoToolsPlugin({ config }) {
  if (!existsSync(skillsDir)) return;

  config.skills = config.skills || {};
  config.skills.paths = config.skills.paths || [];

  if (!config.skills.paths.includes(skillsDir)) {
    config.skills.paths.push(skillsDir);
  }
}
