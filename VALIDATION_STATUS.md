# Validation status

Last architecture update: 2026-07-19.

## Final package state

- Package-code HEAD: `ff04a1148ec65267b656bbf43ddb4dd6f623b1c5`.
- Final package version: `2.1.0~ynh1`.
- The package remains on the current stable official Gitea Runner binary. No Runner packaging logic was changed because the original package workflows were already green.
- The updater rejects prereleases and downgrades, verifies the official SHA-256 file and is idempotent: a second run reported `already-current 2.1.0` with no manifest diff.
- Both workflows use `actions/checkout@v7.0.0` and `actions/setup-python@v6.3.0`.

## Root cause and corrections

- No functional Runner defect was evidenced. The correction was limited to the requested CI modernization and to the updater's whitespace-only field replacement, which keeps generated manifest output deterministic.
- The official YunoHost package linter is executed in CI from a clean checkout and fails on real errors. The fork is not in the public YunoHost catalog, so the workflow accepts only the exact documented `AppCatalog.is_in_catalog` critical result; any other critical result or error remains fatal.

## Commands and evidence

Local Windows checks used the bundled Python runtime and Git Bash because `python3`, Docker and a WSL distribution were unavailable:

```text
<bundled-python> -m py_compile tools/*.py
find scripts -maxdepth 1 -type f ! -name '*.sql' -print0 | sort -z | while IFS= read -r -d '' script; do echo "Checking ${script}"; bash -n "$script"; done
<bundled-python> tools/update_upstream.py
<bundled-python> tools/update_upstream.py   # idempotence: already-current 2.1.0
```

The exact static checks, binary checks and package-linter procedure passed in the remote Linux workflows.

Validation runs for the package-code HEAD:

- Package validation: [run 29695502917](https://github.com/faleious-ai/gitea-runner_ynh/actions/runs/29695502917).
- Update stable upstream release: [run 29695503624](https://github.com/faleious-ai/gitea-runner_ynh/actions/runs/29695503624).

Both runs were green. The package linter accepted only the documented catalog exception. No Node.js 20 warning was present in the final logs.

## Required before production use

On disposable YunoHost 12 infrastructure, validate an unregistered installation, registration against disposable Gitea, a Docker-isolated workflow, upgrade from the legacy package with `.runner` preservation, backup/restore, removal, URL change and reboot health.

## Current classification

`AUTOMATION_AND_PACKAGE_LINTER_VERIFIED_UPSTREAM_PIN_VALIDATED_LIFECYCLE_UNVERIFIED`

The lifecycle is intentionally not classified as verified because no YunoHost host was available in this workspace.

Read `AGENTS.md` and `doc/ADMIN.md` before continuing.
