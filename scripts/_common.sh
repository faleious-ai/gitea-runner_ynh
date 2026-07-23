#!/bin/bash

# Keep the public Gitea hostname reachable from the isolated per-job Docker
# networks created by Gitea Runner. The TLS hostname remains unchanged; only
# Docker name resolution is redirected to the host gateway.
ynh_runner_configure_host_gateway() {
    local config_file="$data_dir/config.yaml"
    local instance_url="${gitea_url:-}"
    if [ -z "$instance_url" ]; then
        instance_url=$(ynh_app_setting_get --key=gitea_url)
    fi

    local instance_host
    instance_host=$(python3 - "$instance_url" <<'PY'
import sys
from urllib.parse import urlsplit

host = urlsplit(sys.argv[1]).hostname or ""
if not host or any(ch.isspace() for ch in host):
    raise SystemExit(1)
print(host)
PY
    ) || ynh_die "Unable to derive the Gitea hostname from gitea_url"

    python3 - "$config_file" "$instance_host" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
host = sys.argv[2]
desired = f"--add-host={host}:host-gateway"
lines = path.read_text(encoding="utf-8").splitlines()
in_container = False
found = False

for index, line in enumerate(lines):
    if line == "container:":
        in_container = True
        continue
    if in_container and line and not line.startswith((" ", "#")):
        break
    if not in_container:
        continue
    match = re.match(r"^(\s{2})options:\s*(.*?)\s*$", line)
    if not match:
        continue
    raw = match.group(2)
    if not raw or raw in {"null", "~"}:
        options = ""
    elif len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        if raw[0] == '"':
            options = json.loads(raw)
        else:
            options = raw[1:-1].replace("''", "'")
    else:
        options = raw
    tokens = options.split()
    tokens = [token for token in tokens if not token.startswith(f"--add-host={host}:")]
    tokens.append(desired)
    lines[index] = f"  options: {json.dumps(' '.join(tokens))}"
    found = True
    break

if not found:
    raise SystemExit("container.options was not found in the generated runner configuration")

path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
PY
}
