"""Mint one OpenAI-format harness key on this cloud computer.

Reads the local owner credential and never prints it. Prints one JSON object
with the public base URL and the new key.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def home() -> Path:
    raw = os.environ.get("HERMES_HOME") or os.environ.get("MISAKA_HOME")
    return Path(raw).expanduser() if raw else Path.home() / ".misaka-agent"


def origin(root: Path) -> str:
    path = root / "pairing" / "public-origin.txt"
    if path.is_file():
        found = path.read_text(encoding="utf-8").strip().rstrip("/")
        if found.startswith("https://"):
            return found
    return "http://127.0.0.1:8765"


def mint(root: Path) -> dict:
    owner_path = root / "pairing" / "owner-token"
    if not owner_path.is_file():
        raise SystemExit("这台电脑还没有云端所有者凭证。先在 MISAKA 里完成一键自动连接。")
    owner = owner_path.read_text(encoding="utf-8").strip()
    request = urllib.request.Request(
        "http://127.0.0.1:8765/v1/harness-keys",
        data=json.dumps({"label": "Cursor"}).encode(),
        method="POST",
        headers={"Authorization": "Bearer " + owner, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise SystemExit("本机 8765 上的云端调度没有开，无法签发钥匙。") from exc
    secret = payload.get("harness_key", {}).get("secret", "")
    key_id = payload.get("harness_key", {}).get("key_id", "")
    if not isinstance(secret, str) or not secret.startswith("misaka-key-"):
        raise SystemExit("云端没有返回接入钥匙。")
    base = origin(root).rstrip("/") + "/v1"
    return {"openai_base": base, "key_id": key_id, "api_key": secret}


def main() -> None:
    print(json.dumps(mint(home()), ensure_ascii=False))


if __name__ == "__main__":
    main()
