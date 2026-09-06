# Getting Started

geno-tools installs agent skillsets, registers their skills with your coding
agents, and keeps each installation current.

## 1. Install geno-tools

Install the Homebrew formula:

```zsh
brew install 42euge/geno/geno-tools
```

Confirm the CLI is available:

```zsh
geno-tools --version
```

## 2. Discover skillsets

Browse the skillsets available from your configured sources:

```zsh
geno-tools discover
```

## 3. Install a skillset

Install by discovered name:

```zsh
geno-tools install geno-tt
```

You can also install directly from a git URL or a local repository:

```zsh
geno-tools install https://github.com/42euge/geno-tt.git
geno-tools install /path/to/your-skillset
```

geno-tools creates an isolated runtime when the skillset needs one and
registers its skills with the supported coding agents detected on your system.

## 4. Verify the installation

```zsh
geno-tools status
```

The status view shows installed versions, selected sources, and remote drift.

## Next steps

Update every installed skillset:

```zsh
geno-tools update
```

Develop against a local checkout without replacing its stable installation:

```zsh
geno-tools dev activate /path/to/your-skillset
geno-tools dev status
geno-tools dev deactivate your-skillset
```
