# Upload Notebook to Google Colab

Upload a Jupyter notebook to Google Drive so it's accessible in Google Colab.

## Input

`$ARGUMENTS` — Path to the `.ipynb` file to upload. Can be absolute or relative to the current working directory.

If no arguments provided, search for `.ipynb` files in the current project and ask the user which one to upload.

## Workflow

### 1. Resolve the notebook

- If `$ARGUMENTS` is provided, resolve it to an absolute path
- If not provided, glob for `**/*.ipynb` (excluding `.venv/`, `node_modules/`, `.ipynb_checkpoints/`) and present the list using `AskUserQuestion`
- Verify the file exists and is valid JSON (valid notebook format)

### 2. Load Google Drive config

Read `~/.genotools/colab/config.json` for the configured account and settings:

```json
{
  "google_account": "user@gmail.com",
  "drive_mount_base": "~/Library/CloudStorage",
  "default_folder": "Colab Notebooks"
}
```

If the config doesn't exist or `google_account` is empty, tell the user to run `/gt-config-colab` first and stop.

Resolve the full Google Drive mount path: `<drive_mount_base>/GoogleDrive-<google_account>/My Drive`

Verify the mount exists. If not, tell the user their Google Drive may not be mounted and suggest running `/gt-config-colab`.

### 3. Choose destination folder

Use the `default_folder` from config as the destination inside Google Drive.

If the folder doesn't exist in the mount, create it.

Ask the user if they want to use the default location or specify a subfolder. Use `AskUserQuestion` with options:

- The configured `default_folder` (default)
- `<default_folder>/<project-name>/` (project subfolder, derived from the current git repo name or directory name)
- Custom path (let user type)

### 4. Copy the notebook

- Copy the `.ipynb` file to the chosen destination
- If a file with the same name already exists, ask the user whether to overwrite or rename (append timestamp)
- Use `cp` (not `mv`) — keep the original in place

### 5. Confirm and provide link

After copying:

- Confirm the file was copied successfully with the full path
- Provide instructions to open in Colab:
  - Go to `https://colab.research.google.com/` → File → Open notebook → Google Drive tab → navigate to the folder
  - Or: open Google Drive in browser, find the file, right-click → Open with → Google Colab
