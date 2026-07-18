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

    for lifecycle in ("install", "upgrade"):
        script_path = ROOT / "scripts" / lifecycle
        script = script_path.read_text(encoding="utf-8")
        if IDENTITY_CONDITION not in script:
            errors.append(f"{lifecycle} must gate service monitoring on persistent runner identity")
        elif SERVICE_ADD not in script:
            errors.append(f"{lifecycle} must add a registered runner to YunoHost monitoring")
        elif script.index(SERVICE_ADD) < script.index(IDENTITY_CONDITION):
            errors.append(f"{lifecycle} monitors the service before runner registration is proven")
        if SERVICE_REMOVE not in script:
            errors.append(f"{lifecycle} must remove unregistered runners from YunoHost monitoring")

    for script in (ROOT / "scripts").iterdir():
        if script.is_file() and b"\r\n" in script.read_bytes():
            errors.append(f"CRLF line endings in {script.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"package-valid version={version} architectures={','.join(manifest['integration']['architectures'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
