# claude-skills-copilot

A thin **marketplace proxy** that makes
[`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills)
installable in **GitHub Copilot CLI / Copilot App**.

## Why this exists

Upstream's `marketplace.json` is *almost* Copilot-compatible. It fails validation
for exactly one reason:

```
Invalid marketplace.json: plugins.9.description: String must contain at most 1024 character(s),
                          plugins.73.description: ...,
                          plugins.74.description: ...
```

Copilot caps plugin `description` at 1024 chars; three entries
(`engineering-advanced-skills`, `research-ops-skills`, `markdown-html-skills`)
exceed it. Nothing else about the repo is incompatible — plugin manifests at
`<plugin>/.claude-plugin/plugin.json` and `skills/<name>/SKILL.md` are both
natively supported by Copilot.

## How it works

This repo contains **no vendored plugin content**. It only ships a rewritten
catalog at `.github/plugin/marketplace.json` where each plugin's `source` points
back at upstream:

```json
{
  "source": { "source": "github", "repo": "alirezarezvani/claude-skills", "ref": "main", "path": "marketing-skill" }
}
```

So plugin content is always fetched live from upstream — this repo never goes
stale on content, only on catalog metadata, which a daily GitHub Action re-syncs.

## Usage

```bash
copilot plugin marketplace add YOUR-USER/claude-skills-copilot
copilot plugin marketplace browse claude-code-skills
copilot plugin install marketing-skills@claude-code-skills
```

Update everything later:

```bash
copilot plugin marketplace update claude-code-skills
copilot plugin update --all
```

### Auto-update on every session

Add to `~/.copilot/config.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-code-skills": {
      "source": { "source": "github", "repo": "YOUR-USER/claude-skills-copilot" },
      "autoUpdate": true
    }
  }
}
```

## Maintenance

`scripts/sync_marketplace.py` fetches upstream's catalog, caps descriptions at
1024 chars, rewrites `source` to remote GitHub objects, and drops any field
Copilot doesn't recognize. `.github/workflows/sync-marketplace.yml` runs it daily
and commits on change.
