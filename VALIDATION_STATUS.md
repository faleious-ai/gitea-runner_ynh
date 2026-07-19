# Validation status

Last architecture update: 2026-07-19.

## Current package state

- Package pin: `2.1.0~ynh1` from the official Gitea download repository.
- Updater hardening was published at commit `7b56b91a73d84316dcb2672f2e766fa6e02a25d4`.
- The updater rejects prereleases and automated downgrades, verifies upstream SHA-256 files against downloaded binaries and stops for manual review if assets are republished under the current version.
- Legacy `act_runner` packaging has been migrated to the official `gitea/runner` layout and stable local binary name `runner`.
- Runner identity and operator configuration are stored in `data_dir` and included in upgrade, backup and restore handling.
- Package tests contain no external registration credential.
- Unregistered installations keep the systemd unit available but are not added to YunoHost service monitoring until `.runner` exists.
- Static validation and scheduled/manual/push-triggered update workflows are present.
- No lifecycle validation run tied to the hardened updater commit has been recorded.

## Required before production use

1. Confirm GitHub Actions is enabled and run package validation on the exact head.
2. Validate an unregistered installation without a live external instance.
3. Register against a disposable Gitea instance and confirm service startup and monitoring.
4. Execute a minimal workflow using Docker isolation.
5. Upgrade from the legacy 0.2.6 package and confirm `.runner` identity preservation.
6. Test backup/restore, removal and reboot health.
7. Record exact commit, workflow run and evidence.

## Current classification

`UPSTREAM_CURRENT_AUTOMATION_HARDENED_LIFECYCLE_UNVERIFIED`

Read `AGENTS.md` and `doc/ADMIN.md` before continuing.
