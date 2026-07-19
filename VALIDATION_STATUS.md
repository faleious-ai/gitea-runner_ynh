# Validation status

Last architecture update: 2026-07-19.

## Current package state

- Package-code HEAD before this status record: `46581a2c4fb097f7457d75efe6408eac727f7220`.
- Current package version: `2.1.0~ynh3`.
- The complete packaging manifest is preserved, including installation arguments, immutable AMD64/ARM64 sources, checksums and YunoHost resources.
- The package remains pinned to the latest stable official Gitea Runner binary `2.1.0` with immutable versioned URLs and SHA-256 values.
- The updater preserves the current `~ynhN` package revision.

## Root causes and corrections

Two consecutive real installation attempts on YunoHost `12.1.40.1`, Debian Bookworm ARM64, exposed obsolete helper names that static CI had not rejected:

1. `2.1.0~ynh1` failed with exit code 127 because `scripts/install` called nonexistent `ynh_add_systemd_config`.
2. `2.1.0~ynh2` successfully downloaded and verified the ARM64 binary, installed Docker, generated `config.yaml`, reached the configured Gitea instance, registered the Runner and created its systemd unit. It then failed with exit code 127 because service startup called nonexistent `ynh_systemd_action`.

The package now:

- uses `ynh_config_add_systemd` to install or refresh the unit;
- uses `ynh_config_remove_systemd` during removal;
- uses `ynh_systemctl` for start and stop actions in install, upgrade and restore;
- rejects `ynh_add_systemd_config`, `ynh_remove_systemd_config` and `ynh_systemd_action` anywhere under `scripts/`;
- requires the current helpers in the relevant lifecycle paths;
- keeps registration optional and never persists the registration credential.

## Validation state

Repository-side validation and the real installation retry for `2.1.0~ynh3` are not yet recorded here. A fresh package-validation run must pass for the exact package-code HEAD, followed by another real YunoHost installation using a newly generated registration credential if the failed attempt left an offline Runner registration.

The real `~ynh2` attempt proved that upstream download, SHA-256 verification, ARM64 execution, Gitea connectivity and registration work. It did not prove successful service startup because the obsolete helper stopped the installer immediately before that step.

## Required next checks

1. Run `Package validation` for package-code HEAD `46581a2c4fb097f7457d75efe6408eac727f7220` or its status-only descendant.
2. Confirm the local validator, Python compilation, shell syntax and official YunoHost package linter pass.
3. Remove any offline duplicate Runner identity created by the failed registered attempt.
4. Install `2.1.0~ynh3` with the real Gitea URL and a valid instance-level registration token.
5. Confirm `systemctl status gitea-runner`, YunoHost service monitoring and the Gitea administration page show the Runner online.
6. Dispatch a disposable Actions workflow using Docker isolation.
7. Later validate upgrade, backup/restore, removal and reboot health.

## Current classification

`REAL_REGISTRATION_VERIFIED_SERVICE_HELPERS_CORRECTED_YNH3_RETEST_REQUIRED`

Read `AGENTS.md` and `doc/ADMIN.md` before continuing.
