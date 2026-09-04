const esbuild = require("esbuild");
const packageJson = require("./package.json");

const production = process.argv.includes("--production");
const watch = process.argv.includes("--watch");
const buildDatetime = new Date().toISOString();
const buildName = process.env.GENO_TOOLS_BUILD_NAME?.trim() || "local build";

async function main() {
  const context = await esbuild.context({
    entryPoints: ["src/extension.ts"],
    bundle: true,
    outfile: "dist/extension.js",
    external: ["vscode"],
    format: "cjs",
    platform: "node",
    target: "node20",
    define: {
      __GENO_TOOLS_VERSION__: JSON.stringify(packageJson.version),
      __GENO_TOOLS_BUILD_DATETIME__: JSON.stringify(buildDatetime),
      __GENO_TOOLS_BUILD_NAME__: JSON.stringify(buildName)
    },
    minify: production,
    sourcemap: !production,
    logLevel: "info"
  });

  if (watch) {
    await context.watch();
  } else {
    await context.rebuild();
    await context.dispose();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
