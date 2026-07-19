# Validation status

Last architecture update: 2026-07-19.

## Final package state

- Package-code HEAD: `8b3b4f8daa5d2a4118b385e574509836d84ccf60`.
- Final package version: `2.1.0~ynh2`.
- The package remains pinned to the latest stable official Gitea Runner binary `2.1.0` with immutable versioned URLs and SHA-256 values.
- The updater preserves the current `~ynhN` package revision. A local rerun reported `already-current 2.1.0` without changing the manifest after the intentional `~ynh2` bump.

## Root cause and corrections

- Installation failed with exit code 127 because `scripts/install` called the nonexistent `ynh_add_systemd_config` helper. `scripts/upgrade` had the same defect, and `scripts/remove` used the obsolete `ynh_remove_systemd_config` spelling.
- The lifecycle scripts now use the YunoHost 12 helpers `ynh_config_add_systemd` and `ynh_config_remove_systemd`.
- The package validator now rejects both obsolete spellings and requires the correct helpers, preventing regression. Registration remains optional; an empty token installs the package without registering or starting the Runner.

## Commands and evidence

Local Windows checks used the bundled Python runtime and Git Bash because `python3`, Docker and a WSL distribution were unavailable:

```text
<bundled-python> tools/validate_package.py
<bundled-python> -m compileall -q tools
for script in scripts/*; do echo Checking $script; bash -n $script; done
rg -n 'ynh_add_systemd_config|ynh_remove_systemd_config' scripts conf
<bundled-python> tools/update_upstream.py
```

Compilation and shell parsing passed locally; the helper scan returned no obsolete names. The standalone validator reported only the checkout's CRLF conversion. The exact validator, binary checks and official YunoHost package-linter procedure passed in the remote Linux workflows.

Validation runs for the package-code HEAD:

- Package validation: [run 29697551580](https://github.com/faleious-ai/gitea-runner_ynh/actions/runs/29697551580).
- Update stable upstream release: [run 29697551484](https://github.com/faleious-ai/gitea-runner_ynh/actions/runs/29697551484).

Both runs were green, including the documented catalog exception from the official package linter. No Node.js 20 warning was present.

## Required before production use

On disposable YunoHost 12 infrastructure, validate an unregistered installation, registration against disposable Gitea, a Docker-isolated workflow, upgrade from the legacy package with `.runner` preservation, backup/restore, removal, URL change and reboot health.

## Current classification

`AUTOMATION_AND_PACKAGE_LINTER_VERIFIED_UPSTREAM_PIN_VALIDATED_LIFECYCLE_UNVERIFIED`

The lifecycle is intentionally not classified as verified because no YunoHost host was available in this workspace.

Read `AGENTS.md` and `doc/ADMIN.md` before continuing.
