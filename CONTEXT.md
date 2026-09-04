# geno-tools

geno-tools manages stable skillset installations and optional development
selections, and can reproduce those selections across configured hosts.

## Language

**Stable fallback**:
The managed checkout, runtime, and skills that `dev deactivate` restores.
_Avoid_: Canonical version, production copy

**Active dev selection**:
The developer checkout, runtime, and skills currently selected instead of the
Stable fallback.
_Avoid_: Installed dev version, dev install

**Dev snapshot**:
A portable representation of an Active dev selection at one moment, including
its Git commit and non-ignored working-tree changes.
_Avoid_: Checkout copy, dirty bundle

**Rollback selection**:
The previous active selection retained when sync changes a skillset selection.
_Avoid_: Backup install

**Sync selection**:
The per-skillset choice of Stable fallback or Active dev selection made for one
sync operation.
_Avoid_: Variant
