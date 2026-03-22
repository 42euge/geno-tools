# Configure Google Colab Integration

Select which Google account and default folder to use for uploading notebooks to Google Colab via Google Drive.

## Input

`$ARGUMENTS` — Optional. Can be:
- A Gmail address to set directly (e.g., `user@gmail.com`)
- `show` to display current config
- Empty to enter interactive selection

## Workflow

### 1. Load current config

Read the config file at `~/.genotools/colab/config.json`. If it doesn't exist, create it with defaults:

```json
{
  "google_account": "",
  "drive_mount_base": "~/Library/CloudStorage",
  "default_folder": "Colab Notebooks"
}
```

Display the current configuration to the user.

### 2. Detect available Google accounts

Scan for mounted Google Drive accounts by listing directories matching `GoogleDrive-*` in the `drive_mount_base` directory (default: `~/Library/CloudStorage/`).

Extract the email from each directory name (e.g., `GoogleDrive-user@gmail.com` → `user@gmail.com`).

If no accounts are found, tell the user to install and sign into Google Drive for Desktop, then stop.

### 3. Select account

If `$ARGUMENTS` contains an email address, validate it matches one of the detected accounts and use it.

Otherwise, use `AskUserQuestion` to present the detected accounts as options. Include:
- Each detected Google account email
- Which one is currently selected (mark with ✓ in the description)

### 4. Configure default folder

After account selection, ask the user if they want to change the default upload folder. Use `AskUserQuestion` with options:

- `Colab Notebooks` (default)
- `Colab Notebooks/<current-project>` (project-specific subfolder)
- Custom (let user type a path)

### 5. Verify and save

- Verify the selected account's Google Drive mount exists and is accessible: check that `<drive_mount_base>/GoogleDrive-<account>/My Drive` is a valid directory
- Verify the default folder exists inside the mount, or create it
- Write the updated config to `~/.genotools/colab/config.json`
- Display the final configuration

### 6. Update README if needed

If `~/.genotools/colab/` is newly created, ensure the `~/.genotools/README.md` structure section includes the `colab/` directory.
