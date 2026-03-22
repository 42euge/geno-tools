# Upload Notebook to Kaggle

Prepare and upload a Jupyter notebook to Kaggle for running with the kaggle-benchmarks SDK.

## Input

`$ARGUMENTS` — Path to the `.ipynb` file to upload. Can be absolute or relative to the current working directory.

If no arguments provided, search for `.ipynb` files in the current project and ask the user which one to upload.

## Workflow

### 1. Resolve the notebook

- If `$ARGUMENTS` is provided, resolve it to an absolute path
- If not provided, glob for `**/*.ipynb` (excluding `.venv/`, `node_modules/`, `.ipynb_checkpoints/`) and present the list using `AskUserQuestion`
- Verify the file exists and is valid JSON (valid notebook format)

### 2. Ensure the repo is public

The notebook clones the repo on Kaggle, so it must be publicly accessible.

- Detect the GitHub remote URL from `git remote -v`
- Check repo visibility using `gh repo view --json visibility`
- If private, ask the user for confirmation, then make it public with `gh repo edit --visibility public --accept-visibility-change-consequences`
- If no remote, warn the user that the notebook may not work on Kaggle without a public repo

### 3. Ensure the notebook is committed and pushed

- Check `git status` for uncommitted changes to the notebook or any files it depends on (e.g., `src/`, `data/`)
- If there are uncommitted changes, commit and push them
- Verify the push succeeded

### 4. Verify notebook setup cell

Read the notebook and check whether its first code cell:
- Handles cloning the repo (e.g., `!git clone` or `subprocess.run(["git", "clone", ...])`)
- Adds `src/` to `sys.path`
- Generates data if missing

If the notebook doesn't handle setup, warn the user that it may not run on Kaggle without modifications.

### 5. Provide Kaggle instructions

Print instructions for uploading to Kaggle:

1. **New benchmark task:** Go to `https://www.kaggle.com/benchmarks/tasks/new`
2. **New notebook:** Go to `https://www.kaggle.com/code/new` → File → Upload Notebook → select the `.ipynb` file
3. **From GitHub (easiest):** The notebook can be imported directly from the public repo URL

Also provide the direct GitHub raw URL for the notebook:
`https://github.com/<owner>/<repo>/blob/main/<path-to-notebook>`

### 6. Optional: Upload via Kaggle API

If the user has the Kaggle API configured (`~/.kaggle/kaggle.json` exists):

- Ask if they want to push via the API using `kaggle kernels push`
- If yes, create/update `kernel-metadata.json` in the notebook's directory:
  ```json
  {
    "id": "<username>/attention-bench",
    "title": "AttentionBench",
    "code_file": "<notebook-filename>",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": true,
    "enable_gpu": false,
    "enable_internet": true,
    "competition_sources": [],
    "dataset_sources": [],
    "kernel_sources": []
  }
  ```
- Run `kaggle kernels push -p <notebook-directory>`
- Report the kernel URL on success
