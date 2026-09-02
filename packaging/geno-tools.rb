# frozen_string_literal: true

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
  url "https://github.com/42euge/geno-tools/archive/refs/tags/v0.10.0.tar.gz"
  sha256 "ee023654ead9929d03c633315019eda988a6f781af32f54d434a936e5bf0e6e9"
  license "MIT"

  head "https://github.com/42euge/geno-tools.git", branch: "main"

  depends_on "libyaml"
  depends_on "node"
  depends_on "python@3.12"

  resource "setuptools" do
    url "https://files.pythonhosted.org/packages/95/9c/c510029fc6ef33a6275cd2c5d3cecd6613dfd6aa401d57c54f1c18852ccf/setuptools-84.0.0-py3-none-any.whl"
    sha256 "51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz"
    sha256 "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/b3/38/89ba8ad64ae25be8de66a6d463314cf1eb366222074cfda9ee839c56a4b4/mdurl-0.1.2-py3-none-any.whl"
    sha256 "84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/94/54/e7d793b573f298e1c9013b8c4dade17d481164aa517d1d7148619c2cedbf/markdown_it_py-4.0.0-py3-none-any.whl"
    sha256 "87327c59b172c5011896038353a81343b6754500a08cd7a4973bb48c6d578147"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/c7/21/705964c7812476f378728bdf590ca4b771ec72385c533964653c68e86bdc/pygments-2.19.2-py3-none-any.whl"
    sha256 "86540386c03d588bb81d44bc3928634ff26449851e99741617ecb9037ee5ec0b"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/82/3b/64d4899d73f91ba49a8c18a8ff3f0ea8f1c1d75481760df8c68ef5235bf5/rich-15.0.0-py3-none-any.whl"
    sha256 "33bd4ef74232fb73fe9279a257718407f169c09b78a87ad3d296f548e27de0bb"
  end

  def install
    # Keep the complete Python environment under the formula prefix. Vendored
    # resources make installation reproducible and avoid resolving packages
    # from PyPI while Homebrew is building the formula.
    ENV["PIP_NO_INDEX"] = "1"
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install resource("setuptools")
    venv.pip_install resource("pyyaml"), build_isolation: false
    %w[mdurl markdown-it-py pygments rich].each do |package|
      venv.pip_install resource(package)
    end
    venv.pip_install_and_link buildpath, build_isolation: false
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
