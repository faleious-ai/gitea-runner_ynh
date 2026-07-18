# Validation status

Last architecture update: 2026-07-18.

## Current package state

- Package pin: `2.1.0~ynh1` from the official Gitea download repository.
- The automated updater has already produced the immutable 2.1.0 URLs and SHA-256 values.
- Legacy `act_runner` packaging has been migrated to the official `gitea/runner` layout and stable local binary name `runner`.
- Runner identity and configuration are stored in `data_dir` and included in upgrade, backup and restore handling.
- Package tests no longer contain an external registration credential.
- Static validation and scheduled/manual update workflows are present.

## Known validation gate

The current install script adds the YunoHost service entry before it checks whether registration created `.runner`. The systemd unit itself is gated by `ConditionPathExists`, but an unregistered package installation may still appear as a monitored inactive service. Correct this locally if package CI treats that as a failure, then keep service monitoring conditional on `.runner`, as already implemented in upgrade and restore.

## Required before production use

1. Run package validation on the exact head.
2. Validate an unregistered installation without a live external instance.
3. Register against a disposable Gitea instance and confirm service startup.
4. Execute a minimal workflow using Docker isolation.
5. Upgrade from the legacy 0.2.6 package and confirm `.runner` identity preservation.
6. Test backup/restore, removal and reboot health.
7. Record exact commit, workflow run and evidence.

## Current classification

`UPSTREAM_UPDATED_LIFECYCLE_UNVERIFIED`

Read `AGENTS.md` and `doc/ADMIN.md` before continuing.