# Homebrew formula for geno-tools (+ geno-tt).
#
# Source of truth lives in the geno-tools repo; the 42euge/homebrew-geno tap
# should sync this file. Scope: geno-tools and geno-tt ONLY. The `geno` go
# binary (from 42euge/geno-cli) and the other ecosystem tools (vault/surf/
# pear/specs) are intentionally out of scope here.
#
# WHY THIS IS A REWRITE
# ---------------------
# The previous `geno` formula ran `pipx install …` inside `def install`. Brew
# executes that phase in a build sandbox whose $HOME/$PIPX_HOME is a throwaway
# temp dir — pipx reported success, then brew discarded the venvs, so nothing
# landed in ~/.local/pipx and `geno-tools: command not found`. Only the go
# binary survived because it was the one thing written to the formula prefix.
#
# The fix: install the Python tools into the formula's OWN prefix (libexec),
# which brew keeps, using the idiomatic Language::Python::Virtualenv helper —
# no pipx, no user-HOME dependency, nothing to discard.

class GenoTools < Formula
  include Language::Python::Virtualenv

  desc "Unified control plane for AI coding agents — resolve, scope, launch (+ tt workspaces)"
  homepage "https://github.com/42euge/geno-tools"
  license "MIT"

  # TODO(release): pin a tagged tarball + sha256 once v0.7.0 is pushed/tagged.
  #   url "https://github.com/42euge/geno-tools/archive/refs/tags/v0.7.0.tar.gz"
  #   sha256 "…"
  # Until then, build from the default branch:
  head "https://github.com/42euge/geno-tools.git", branch: "main"
  version "0.7.0"

  depends_on "python@3.12"

  # geno-tt (the `tt` workspace CLI) is installed into the same venv.
  # Pinned by release; use HEAD until tagged.
  resource "geno-tt" do
    url "https://github.com/42euge/geno-tt.git", using: :git, branch: "main"
  end

  def install
    # A single venv under the formula prefix (libexec) — persisted by brew,
    # unlike ~/.local/pipx which the build sandbox redirects and discards.
    venv = virtualenv_create(libexec, "python3.12")

    # geno-tools itself (pulls its declared deps: pyyaml, click). Bundles the
    # geno-iso container CLI (geno_tools/iso) in the same package.
    system libexec/"bin/pip", "install", "--verbose", buildpath

    # geno-tt with its iTerm2 orchestration extra so `tt` integration works.
    resource("geno-tt").stage do
      system libexec/"bin/pip", "install", "--verbose", ".[orchestration]"
    end

    # Expose the entry points on PATH. geno-tools ships four; geno-tt ships tt.
    %w[geno-tools geno-trace geno-docs geno-iso tt].each do |exe|
      bin.install_symlink libexec/"bin/#{exe}"
    end
  end

  def caveats
    <<~EOS
      Installed the geno control plane:
        geno-tools   — resolve · scope · launch skillset bundles (npx does registration)
        geno-iso     — isolated agent containers (bundled with geno-tools)
        geno-trace   — skill telemetry / health
        geno-docs    — skill docs compiler
        tt           — iTerm2 + workspace orchestration (geno-tt)

      Register geno skills with your coding agents:
        geno-tools install-agent

      Workspaces (the code-org scheme, via `tt`):
        ~/code/<track>/<domain>/<workspace>.<born>/<repo>
        tt new-project <track>.<domain>.<workspace>
        tt inv

      `tt`'s iTerm2 integration needs the Python API enabled:
        iTerm2 ▸ Settings ▸ General ▸ Magic ▸ Enable Python API

      To remove everything geno-tools installed (keeps your data):
        geno-tools uninstall
        brew uninstall geno-tools
    EOS
  end

  test do
    assert_match "0.7.0", shell_output("#{bin}/geno-tools --version")
    system bin/"geno-iso", "--help"
    # `tt --version` is NOT valid — tt treats it as a session name. Use --help.
    assert_match "workspace", shell_output("#{bin}/tt --help")
  end
end
