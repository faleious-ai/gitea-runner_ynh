# AGENTS.md

## Mission

Maintain the YunoHost package for the official Gitea Runner. Track the newest stable upstream release that passes package validation. Resolve “latest” only in the update workflow; installation must use a versioned asset and committed SHA-256.

## Read before changing

1. `manifest.toml`, `tests.toml`, `scripts/`, `conf/` and this file.
2. Runner releases and source: https://gitea.com/gitea/runner
3. Runner administration documentation: https://docs.gitea.com/usage/actions/runner
4. Gitea Actions documentation: https://docs.gitea.com/usage/actions
5. Gitea release notes: https://blog.gitea.com/tags/release/
6. YunoHost packaging documentation: https://doc.yunohost.org/packaging_apps
7. Sibling packages:
   - https://github.com/faleious-ai/gitea_ynh
   - https://github.com/faleious-ai/gitea-mcp_ynh

## Why the package is structured this way

The original package installed `act_runner 0.2.6`. Upstream renamed the project to `gitea/runner`, reset stable versioning at 1.0 and renamed the product Gitea Runner. The package installs the upstream binary under the stable local name `runner`, so future upstream filename changes do not affect service paths.

Runtime state belongs in `data_dir`:

- `.runner` is the registered identity and must survive upgrades and backup/restore.
- `config.yaml` is operator configuration and must not be overwritten on upgrade.
- `install_dir` contains only replaceable program files.

Registration is optional at installation. This allows deterministic package CI and staged deployments. When a registration credential is supplied, it is consumed once and never stored by the package. Never commit a real credential to `tests.toml` or any other file.

Job containers use isolated Docker networks. Keep `container.options` reconciled with `--add-host=<gitea-host>:host-gateway` so checkout can reach a Gitea instance hosted on the same machine without changing the TLS hostname.

## Update policy

- Stable semantic versions only; reject prerelease and nightly builds.
- Use raw official Linux binaries from the release API.
- Keep immutable URLs and SHA-256 values in `manifest.toml`.
- Do not silently remove an architecture. Record upstream availability and update tests in the same change.
- Review Runner breaking changes and the Gitea compatibility requirement before publication. Gitea 1.27 and Runner 2.x are the baseline pair for the complete current Actions capability set.
- The upstream updater must preserve the current `~ynhN` package revision when refreshing an upstream version or normalizing immutable pins.

## Required validation

```bash
python3 tools/validate_package.py
python3 -m py_compile tools/*.py
find scripts -maxdepth 1 -type f -print0 |
  sort -z |
  while IFS= read -r -d '' script; do
    echo "Checking ${script}"
    bash -n "$script"
  done
```

The GitHub workflows also run the current official `YunoHost/package_linter`
procedure: clone the linter, create a virtual environment, install its
`requirements.txt` and invoke `package_linter.py` against this package.

YunoHost helpers 2.1 use `ynh_app_upstream_version_changed` to distinguish an upstream binary update from a package-only revision. Do not use the removed v1 helper `ynh_check_app_version_changed`.

YunoHost 12 systemd helpers are named `ynh_config_add_systemd`,
`ynh_config_remove_systemd` and `ynh_systemctl`. Keep the obsolete
`ynh_add_systemd_config`, `ynh_remove_systemd_config` and `ynh_systemd_action`
spellings out of every lifecycle script; the local validator enforces this
contract.

Because this fork is intentionally maintained outside the YunoHost application
catalog, CI permits only the linter's `AppCatalog.is_in_catalog` result for
this repository. Any other linter error or critical result remains fatal.

Package lifecycle validation must cover unregistered install, registered service startup against a disposable Gitea instance, upgrade preserving `.runner`, a minimal workflow job, backup/restore and removal. Do not claim CI or lifecycle success without evidence tied to an exact commit.

## Automation

- `tools/update_upstream.py` queries the official Gitea release API, selects stable raw binaries, hashes them and updates `manifest.toml`.
- `.github/workflows/upstream-update.yml` runs scheduled and manual updates.
- `.github/workflows/package-ci.yml` validates every push and pull request.
- Generated README files are maintained by YunoHost tooling and must not be edited manually.

## Security

The runner executes repository-controlled code. Prefer Docker isolation, do not attach it to untrusted repositories, do not expose the Docker socket beyond the dedicated service account, and never place external credentials directly in workflow files. Keep systemd hardening compatible with Docker access; options such as private devices or namespace denial can break container execution.
