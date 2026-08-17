#!/usr/bin/env python3
"""Sync the upstream Claude Code marketplace catalog into a Copilot-valid marketplace.json.

Upstream: alirezarezvani/claude-skills (.claude-plugin/marketplace.json)

Two transforms are applied:
  1. `description` is capped at 1024 chars (Copilot CLI schema limit; upstream
     currently violates this on 3 entries, which makes the whole file rejected).
  2. `source` is rewritten from a repo-relative path into a remote GitHub source
     object, so plugin content is always pulled straight from upstream instead of
     being vendored into this repo.
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.request

UPSTREAM_REPO = "alirezarezvani/claude-skills"
UPSTREAM_REF = "main"
UPSTREAM_URL = (
    f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_REF}"
    "/.claude-plugin/marketplace.json"
)

MAX_DESCRIPTION = 1024
ELLIPSIS = "\u2026"

OUT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / ".github" / "plugin" / "marketplace.json"
)

# Fields Copilot accepts on a plugin entry. Anything else is dropped so a future
# upstream addition can never break validation again.
ALLOWED_PLUGIN_FIELDS = {
    "name", "source", "description", "version", "author", "homepage",
    "repository", "license", "keywords", "category", "tags",
    "commands", "agents", "skills", "hooks", "mcpServers", "lspServers", "strict",
}


def cap(text: str | None, limit: int) -> str | None:
    if not text or len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + ELLIPSIS


def to_remote_source(source):
    """Turn './some/path' into a GitHub source object pointing at upstream."""
    if not isinstance(source, str):
        return source
    path = source.lstrip("./").strip("/")
    remote = {"source": "github", "repo": UPSTREAM_REPO, "ref": UPSTREAM_REF}
    if path:
        remote["path"] = path
    return remote


def main() -> int:
    with urllib.request.urlopen(UPSTREAM_URL, timeout=60) as resp:
        upstream = json.load(resp)

    plugins = []
    for entry in upstream.get("plugins", []):
        clean = {k: v for k, v in entry.items() if k in ALLOWED_PLUGIN_FIELDS}
        clean["source"] = to_remote_source(clean.get("source"))
        if "description" in clean:
            clean["description"] = cap(clean["description"], MAX_DESCRIPTION)
        plugins.append(clean)

    metadata = dict(upstream.get("metadata") or {})
    metadata["description"] = cap(
        metadata.get("description") or f"Copilot CLI mirror of {UPSTREAM_REPO}.",
        MAX_DESCRIPTION,
    )

    result = {
        "name": upstream.get("name", "claude-code-skills"),
        "owner": upstream.get("owner", {"name": "Alireza Rezvani"}),
        "metadata": metadata,
        "plugins": plugins,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(plugins)} plugins to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
