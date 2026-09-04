# Synchronize dev state as Git-aware snapshots

Sync represents active development state as a Git bundle plus staged,
unstaged, and non-ignored untracked working-tree changes. This preserves dirty
and unpublished work without copying Git administration paths, ignored secrets,
or machine-specific venvs; whole-directory archives were rejected because they
would copy unsafe machine-local state, and requiring users to publish first
would not synchronize the system they are actually using.
