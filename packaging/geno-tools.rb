# Homebrew formula for geno-tools.
#
# Source of truth lives in the geno-tools repo; the 42euge/homebrew-geno tap
# syncs this file. Scope: geno-tools ONLY.
#
# Explicitly OUT of scope (each installs itself):
#   - the `geno` go binary (42euge/geno-cli)
#   - geno-tt (`tt`) and the rest of the ecosystem (vault/surf/pear/specs)
#
# The tap's old `geno.rb` bundled all of the above by shelling out to `pipx
# install` from `def install`. That never worked: brew runs the install phase
# in a sandbox whose $HOME/$PIPX_HOME is a throwaway temp dir, so pipx
# reported success and brew then discarded the venvs — `geno-tools: command
# not found`. Only the go binary survived, because it was the one thing
# written to the formula prefix. Delete geno.rb from the tap; this replaces it.
#
# The fix here: install into the formula's OWN prefix (libexec) via the
# idiomatic Language::Python::Virtualenv helper. No pipx, no dependency on
# the user's HOME, nothing for brew to throw away.

class GenoTools < Formula
  include Language::Python::Virtualenv

  desc "Control plane for AI coding agents: resolve and scope skillset bundles"
  homepage "https://github.com/42euge/geno-tools"
  license "MIT"

  # TODO(release): pin a tagged tarball + sha256 once v0.8.0 is pushed/tagged.
  #   url "https://github.com/42euge/geno-tools/archive/refs/tags/v0.8.0.tar.gz"
  #   sha256 "…"
  # Until then, build from the default branch:
  head "https://github.com/42euge/geno-tools.git", branch: "main"
  version "0.8.0"

  depends_on "python@3.12"

  def install
    # A single venv under the formula prefix (libexec) — persisted by brew,
    # unlike ~/.local/pipx which the build sandbox redirects and discards.
    #
    # NOTE: deliberately NOT using `resource` blocks +
    # virtualenv_install_with_resources. That path installs every dep with
    # `--no-binary :all:`, which makes pip build pyyaml from its sdist — and
    # pyyaml 6.x's sdist needs Cython as a build dep, which fails in the brew
    # sandbox. pip_install on the source tree resolves pyyaml/click as wheels
    # instead. (This formula lives in a personal tap, so the homebrew-core
    # "all deps vendored as resources" rule doesn't bind.)
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install buildpath

    # pip_install leaves the console scripts in libexec/bin, which is NOT on
    # PATH. virtualenv_install_with_resources would link them for us; since we
    # can't use it (see above), link them ourselves.
    bin.install_symlink libexec/"bin/geno-tools"
  end

  def caveats
    <<~EOS
      Installed:
        geno-tools   — resolve and scope skillset bundles (npx does registration)

      Installing a skillset is what registers skills with your agents:
        geno-tools skills discover
        geno-tools skills install <name>
        geno-tools status

      The rest of the geno ecosystem is packaged separately and is NOT
      installed by this formula — notably `tt` (geno-tt) and the `geno` binary.

      To remove:
        geno-tools skills remove <name>   # unregisters skills; do this first
        brew uninstall geno-tools
      Skillset state under ~/.geno is left in place either way.
    EOS
  end

  test do
    assert_match "geno-tools #{version}", shell_output("#{bin}/geno-tools --version")
    # `status` is the cheapest real command: reads ~/.geno, exits 0 when empty.
    assert_match "installed", shell_output("#{bin}/geno-tools status")
  end
end
