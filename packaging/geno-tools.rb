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
  url "https://github.com/42euge/geno-tools/archive/refs/tags/v0.9.0.tar.gz"
  sha256 "3d1b741a491d2f23720b7c818ebfd512af9f700b79e67ca985ebd670d40add60"
  license "MIT"

  head "https://github.com/42euge/geno-tools.git", branch: "main"

  depends_on "libyaml"
  depends_on "node"
  depends_on "python@3.12"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz"
    sha256 "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz"
    sha256 "bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/5b/f5/4ec618ed16cc4f8fb3b701563655a69816155e79e24a17b651541804721d/markdown_it_py-4.0.0.tar.gz"
    sha256 "cb0a2b4aa34f932c007117b194e945bd74e0ec24133ceb5bac59009cda1cb9f3"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/b0/77/a5b8c569bf593b0140bde72ea885a803b82086995367bf2037de0159d924/pygments-2.19.2.tar.gz"
    sha256 "636cb2477cec7f8952536970bc533bc43743542f70392ae026374600add5b887"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/c0/8f/0722ca900cc807c13a6a0c696dacf35430f72e0ec571c4275d2371fca3e9/rich-15.0.0.tar.gz"
    sha256 "edd07a4824c6b40189fb7ac9bc4c52536e9780fbbfbddf6f1e2502c31b068c36"
  end

  def install
    # Keep the complete Python environment under the formula prefix. Vendored
    # resources make installation reproducible and avoid resolving packages
    # from PyPI while Homebrew is building the formula.
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Installed:
        geno-tools   — resolve and scope skillset bundles (npx does registration)

      Installing a skillset is what registers skills with your agents:
        geno-tools discover
        geno-tools install <name>
        geno-tools status

      The rest of the geno ecosystem is packaged separately and is NOT
      installed by this formula — notably `tt` (geno-tt) and the `geno` binary.

      To remove:
        geno-tools system uninstall
        brew uninstall geno-tools
      Skillset state under ~/.geno is left in place either way.
    EOS
  end

  test do
    assert_match(/\Ageno-tools \d+\.\d+\.\d+\n\z/, shell_output("#{bin}/geno-tools --version"))
    # `status` is the cheapest real command: reads ~/.geno, exits 0 when empty.
    assert_match "installed", shell_output("#{bin}/geno-tools status")
  end
end
