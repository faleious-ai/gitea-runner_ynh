#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+~ynh\d+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN = ("/latest/", "nightly", "-rc", "-beta", "-alpha")
IDENTITY_CONDITION = 'if [ -f "$data_dir/.runner" ]; then'
SERVICE_ADD = 'yunohost service add "$app"'
SERVICE_REMOVE = 'yunohost service remove "$app"'
SYSTEMD_ADD = "ynh_config_add_systemd"
SYSTEMD_REMOVE = "ynh_config_remove_systemd"
SYSTEMCTL = "ynh_systemctl"
OBSOLETE_HELPERS = {
    "ynh_check_app_version_changed": "ynh_app_upstream_version_changed",
    "ynh_add_systemd_config": SYSTEMD_ADD,
    "ynh_remove_systemd_config": SYSTEMD_REMOVE,
    "ynh_systemd_action": SYSTEMCTL,
}


def main() -> int:
    errors: list[str] = []
    manifest = tomllib.loads((ROOT / "manifest.toml").read_text(encoding="utf-8"))
    tests = tomllib.loads((ROOT / "tests.toml").read_text(encoding="utf-8"))
    version = str(manifest.get("version", ""))
    if not SEMVER.fullmatch(version):
        errors.append(f"invalid version: {version}")
    upstream_version = version.split("~", 1)[0]

    source = manifest.get("resources", {}).get("sources", {}).get("main", {})
    if source.get("rename") != "runner" or source.get("extract") is not False:
        errors.append("source must be an uncompressed binary renamed to runner")
    for architecture in manifest.get("integration", {}).get("architectures", []):
        item = source.get(architecture)
        if not isinstance(item, dict):
            errors.append(f"missing source for {architecture}")
            continue
        url = str(item.get("url", ""))
        digest = str(item.get("sha256", ""))
        if upstream_version not in url:
            errors.append(f"{architecture} URL does not contain version {upstream_version}")
        if any(marker in url.lower() for marker in FORBIDDEN):
            errors.append(f"mutable or prerelease source for {architecture}")
        if not SHA256.fullmatch(digest):
            errors.append(f"invalid SHA-256 for {architecture}")

    token = str(tests.get("default", {}).get("args", {}).get("token", ""))
    if token:
        errors.append("tests.toml must not contain a registration credential")

    service = (ROOT / "conf/systemd.service").read_text(encoding="utf-8")
    if "__INSTALL_DIR__/runner" not in service or "__DATA_DIR__/.runner" not in service:
        errors.append("systemd service must use stable binary path and persistent identity")
    if "PrivateDevices=yes" in service or "RestrictNamespaces=yes" in service:
        errors.append("systemd hardening blocks Docker execution")
    if "Environment=HOME=__DATA_DIR__" not in service:
        errors.append("systemd service must direct HOME to the writable data directory")
    if "Environment=XDG_CACHE_HOME=__DATA_DIR__/.cache" not in service:
        errors.append("systemd service must direct action cache to the writable data directory")
    if "ReadWritePaths=__DATA_DIR__" not in service:
        errors.append("systemd service must allow writes to data_dir")

    common = (ROOT / "scripts/_common.sh").read_text(encoding="utf-8")
    for required in (
        "ynh_runner_configure_host_gateway",
        "--add-host={host}:host-gateway",
        "container.options was not found",
    ):
        if required not in common:
            errors.append(f"runner network reconciliation missing {required}")

    scripts: dict[str, str] = {}
    for script_path in (ROOT / "scripts").iterdir():
        if not script_path.is_file():
            continue
        script = script_path.read_text(encoding="utf-8")
        scripts[script_path.name] = script
        for obsolete, replacement in OBSOLETE_HELPERS.items():
            if obsolete in script:
                errors.append(
                    f"scripts/{script_path.name} uses obsolete {obsolete}; use {replacement}"
                )
        if b"\r\n" in script_path.read_bytes():
            errors.append(f"CRLF line endings in {script_path.relative_to(ROOT)}")

    upgrade_script = scripts["upgrade"]
    if "ynh_app_upstream_version_changed" not in upgrade_script:
        errors.append("upgrade must use ynh_app_upstream_version_changed")

    for lifecycle in ("install", "upgrade", "restore"):
        if "ynh_runner_configure_host_gateway" not in scripts[lifecycle]:
            errors.append(f"{lifecycle} must reconcile the Gitea host gateway mapping")

    for lifecycle in ("install", "upgrade"):
        script = scripts[lifecycle]
        if SYSTEMD_ADD not in script:
            errors.append(f"{lifecycle} must use {SYSTEMD_ADD}")
        if SYSTEMCTL not in script:
            errors.append(f"{lifecycle} must use {SYSTEMCTL} for service lifecycle actions")
        if IDENTITY_CONDITION not in script:
            errors.append(f"{lifecycle} must gate service monitoring on persistent runner identity")
        elif SERVICE_ADD not in script:
            errors.append(f"{lifecycle} must add a registered runner to YunoHost monitoring")
        elif script.index(SERVICE_ADD) < script.index(IDENTITY_CONDITION):
            errors.append(f"{lifecycle} monitors the service before runner registration is proven")
        if SERVICE_REMOVE not in script:
            errors.append(f"{lifecycle} must remove unregistered runners from YunoHost monitoring")

    restore_script = scripts["restore"]
    if SYSTEMCTL not in restore_script:
        errors.append("restore must use ynh_systemctl to start a registered runner")
    if SYSTEMD_ADD not in restore_script:
        errors.append("restore must regenerate the systemd unit")
    if "/etc/systemd/system" in restore_script:
        errors.append("restore must not restore generated systemd configuration")

    remove_script = scripts["remove"]
    if SYSTEMD_REMOVE not in remove_script:
        errors.append(f"remove must use {SYSTEMD_REMOVE}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"package-valid version={version} architectures={','.join(manifest['integration']['architectures'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
