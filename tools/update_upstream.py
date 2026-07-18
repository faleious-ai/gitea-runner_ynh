#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.toml"
API = "https://gitea.com/api/v1/repos/gitea/runner/releases/latest"
ARCH_ALIASES = {
    "amd64": ("amd64", "x86_64"),
    "arm64": ("arm64", "aarch64"),
}
REJECT_SUFFIXES = (".sha256", ".sha512", ".sig", ".asc", ".json", ".tar.gz", ".tgz", ".zip")


def request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "gitea-runner-ynh-updater"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download_sha256(url: str, destination: Path) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "gitea-runner-ynh-updater"})
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()


def select_binary(assets: list[dict], architecture: str) -> dict:
    aliases = ARCH_ALIASES[architecture]
    matches = []
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        if "linux" not in name or not any(alias in name for alias in aliases):
            continue
        if name.endswith(REJECT_SUFFIXES) or any(word in name for word in ("debug", "checksums", "nightly")):
            continue
        matches.append(asset)
    if len(matches) != 1:
        names = [str(asset.get("name")) for asset in assets]
        raise RuntimeError(f"expected one raw {architecture} binary, found {[item.get('name') for item in matches]}; assets={names}")
    return matches[0]


def replace_field(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf'(?m)^(\s*{re.escape(key)}\s*=\s*)"[^"]*"\s*$')
    updated, count = pattern.subn(rf'\1"{value}"', text, count=1)
    if count != 1:
        raise RuntimeError(f"unable to update {key}")
    return updated


def main() -> int:
    release = request_json(API)
    tag = str(release.get("tag_name", ""))
    if release.get("draft") or release.get("prerelease") or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise RuntimeError(f"latest release is not stable semver: {tag!r}")
    version = tag[1:]
    assets = list(release.get("assets") or [])
    selected = {architecture: select_binary(assets, architecture) for architecture in ARCH_ALIASES}

    hashes: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="gitea-runner-ynh-") as temp_dir:
        temp = Path(temp_dir)
        for architecture, asset in selected.items():
            url = str(asset.get("browser_download_url") or asset.get("url") or "")
            if not url.startswith("https://gitea.com/gitea/runner/releases/download/"):
                raise RuntimeError(f"unexpected release URL for {architecture}: {url}")
            hashes[architecture] = download_sha256(url, temp / str(asset["name"]))

    text = MANIFEST.read_text(encoding="utf-8")
    current_match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    if not current_match:
        raise RuntimeError("manifest version not found")
    current = current_match.group(1).split("~", 1)[0]
    if current == version:
        print(f"already-current {version}")
        return 0

    text = replace_field(text, "version", f"{version}~ynh1")
    for architecture, asset in selected.items():
        url = str(asset.get("browser_download_url") or asset.get("url"))
        text = replace_field(text, f"{architecture}.url", url)
        text = replace_field(text, f"{architecture}.sha256", hashes[architecture])
    MANIFEST.write_text(text, encoding="utf-8")
    print(f"updated {current} -> {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
