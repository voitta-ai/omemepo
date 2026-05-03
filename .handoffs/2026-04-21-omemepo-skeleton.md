# Handoff: omemepo skeleton

**Created:** 2026-04-21
**Author:** Claude Code session (with Greg)
**For:** AI Agent / future self — next iteration
**Status:** Ready to execute — one structural decision pending before push

---

## Summary

Started `omemepo` — a portability and sharing layer for Claude Code. Name is
*omnia mea mecum porto* ("all that is mine, I carry with me"). Dual, co-equal
audience: (a) personal portability — pack/unpack your whole `~/.claude/`,
(b) Voitta-curated Claude Code marketplace shipped in the same repo.
Skeleton is built and validated, CLI stubs run. Next: resolve a repo-structure
mismatch, push, then implement `pack`.

## Project Context

**Tech stack:** Python 3.11+, typer CLI, hatchling build, pipx/uv distribution.

**Repo on GitHub:** `voitta-ai/omemepo` (already exists, one "first commit"
with only a 10-byte `# omemepo` README).

**Local working tree:** `$HOME/g/git.voitta/` is the git clone of the remote.
Sibling voitta projects (voitta-rag, voitta-yolt, truffaldino, jetbrains-voitta,
llm-tldr) are separate clones checked out in the same parent dir; each has its
own `.git` and appears as untracked in `git status` of the parent.

**User's global CLAUDE.md rules that matter here:** voitta-ai repos live under
`$HOME/g/git.voitta/`; always `--no-pager` on git; always `--no-cli-pager` on
AWS; never have expressions in `return` statements; specific imports only; no
tabs in multiline strings; no emoji in code.

## The Plan

### Two co-equal use cases, one repo

**Use case 1 — personal portability (no marketplace needed):**
```bash
omemepo pack --redact-secrets -o profile.tar.gz    # old box
omemepo unpack profile.tar.gz                      # new box
```
Carries `~/.claude/{skills,agents,commands,hooks,CLAUDE.md,plugins,MCP configs}`.
Secrets redacted on pack. Ephemera (history, sessions, caches) excluded.

**Use case 2 — shared marketplace (no tool needed):**
```
/plugin marketplace add voitta-ai/omemepo
/plugin install voitta-misc
```
Stock Claude Code flow. Omemepo CLI is not required to consume.

### Target repo layout (after the pending structural move)

```
omemepo/                                       # = $HOME/g/git.voitta/
├── .claude-plugin/marketplace.json            # must be at repo root
├── plugins/voitta-misc/
│   ├── .claude-plugin/plugin.json
│   └── README.md
├── src/omemepo/{__init__,__main__,cli}.py     # typer app
├── docs/architecture.md                       # all decisions captured
├── pyproject.toml
├── README.md
└── .gitignore
```

### Other Voitta projects as plugins

Existing Voitta MCP services ship plugin entries here to provide Claude
Code-side glue; service lifecycle stays in their own repos:

- `voitta-rag` — self-hosted RAG MCP
- `voitta-yolt` — Claude Code safety hook
- `jetbrains-voitta` — IntelliJ MCP bridge
- `llm-tldr` — code-structure MCP
- `truffaldino` — its Claude Code slice may move entirely into `omemepo mcp`;
  truffaldino keeps multi-tool (Cline/Cursor/IntelliJ) scope

## Key Files

| File | Why It Matters |
|------|---------------|
| `docs/architecture.md` | Full design record incl. open questions |
| `src/omemepo/cli.py` | CLI surface — 6 stub commands via typer |
| `.claude-plugin/marketplace.json` | Claude Code marketplace manifest |
| `plugins/voitta-misc/.claude-plugin/plugin.json` | First (stub) plugin |
| `pyproject.toml` | Deps (typer only), entry point `omemepo = "omemepo.cli:app"` |

## Current State

**Done:**
- Repo skeleton created at `$HOME/g/git.voitta/voitta-omemepo/`
- Marketplace manifest + one plugin stub (`voitta-misc`)
- CLI with 6 commands: `pack`, `unpack`, `publish`, `diff`, `mcp`, `version`.
  Only `version` has real impl; rest exit 1 with "not implemented yet" prints.
- `docs/architecture.md` captures all decisions + open questions
- Smoke test confirmed: `PYTHONPATH=src python3 -m omemepo version` prints `0.0.1`
- typer 0.21.1 available globally — no install needed for smoke tests
- JSON manifests validated, `pyproject.toml` parses, Python compiles
- Schemas verified against real marketplaces under
  `~/.claude/plugins/marketplaces/{openai-codex,every-marketplace,claude-handoff}/`

**In Progress — blocker for push:**
- **Structural mismatch not yet resolved.** Skeleton lives in
  `$HOME/g/git.voitta/voitta-omemepo/` but the git repo root is one level up
  at `$HOME/g/git.voitta/` and its remote is `voitta-ai/omemepo` (no `voitta-`
  prefix). Claude Code requires `.claude-plugin/marketplace.json` at repo
  ROOT, so the current path makes the marketplace unreachable. User was asked
  to confirm moving content up one level; `/handoff` was invoked before they
  answered.

**Not Started:**
- Real impls of `pack`, `unpack`, `publish`, `diff`, `mcp`
- MCP server (omemepo exposing its own tools via MCP)
- Themed plugins beyond `voitta-misc` (planned: `voitta-aws`, `voitta-git`,
  `voitta-debug`, `voitta-infra`)
- `CODEOWNERS`, CI, `LICENSE`
- Secret detection/redaction rules
- Reuse of truffaldino Python code for MCP sync

## Decisions Made — do not re-litigate

- **Combined repo** (tool + marketplace in one) — branding/contribution
  unity, one URL to remember. Rejected: separate `voitta-ai/claude-marketplace`
  sibling repo.
- **Invariant preserved:** the `plugins/` tree must never require code in
  `src/` to install. The tool is additive; the marketplace stands alone.
- **Themed plugins**, currently only `voitta-misc` registered. Themes split
  off as content accumulates. Rejected: per-skill (too noisy) and mega plugin
  (no opt-out).
- **Python 3.11+ with typer** — stack fit with voitta-rag/truffaldino, direct
  code reuse from truffaldino, mature MCP SDK, familiar to Voitta contributors.
  Rejected: Go (single-binary wasn't worth losing code reuse), Node (stack
  mismatch).
- **Subsume truffaldino for Claude Code only** — truffaldino keeps its
  cross-tool (Cline/Cursor/IntelliJ) scope; omemepo takes over the Claude Code
  slice.
- **Claude Code is the sole v1 target.** Claude Desktop and broader AI-tool
  support are filed nice-to-haves, explicitly out of scope for v1.
- **Hybrid publish model**: outside contributors PR-reviewed, listed
  maintainers push direct, `CODEOWNERS` per plugin directory.
- **pipx/uv distribution** over single-binary.

## Important Context

- **The repo on GitHub is `voitta-ai/omemepo`, NOT `voitta-ai/voitta-omemepo`.**
  The skeleton's README, architecture.md, and plugin manifests all say
  `voitta-ai/voitta-omemepo` — must be fixed as part of the push step.
- **The parent dir `git.voitta/` IS the git repo**, remote `voitta-ai/omemepo`.
  The "first commit" (`2eed006`) contains only a 10-byte `# omemepo` README
  at the repo root.
- **Many sibling voitta-ai repos are cloned side-by-side** inside `git.voitta/`
  but are separate repos; they appear as untracked entries in `git status`
  of the parent and should NOT be added.
- **Claude Code marketplace schema inspection** was done against three real
  marketplaces on this box — don't invent fields, our manifests match exactly.
- **User feedback pattern:** prefers free-text answers over `AskUserQuestion`
  forms; wants concise responses; corrects if I over-pitch one side of a
  design.

## Next Steps

1. **Resolve the repo-structure mismatch.** Re-ask user OR, if confirmed,
   execute from `$HOME/g/git.voitta/`:
   ```bash
   cd $HOME/g/git.voitta
   rm README.md                              # 10-byte placeholder
   mv voitta-omemepo/.gitignore .
   mv voitta-omemepo/.claude-plugin .
   mv voitta-omemepo/.handoffs .
   mv voitta-omemepo/plugins .
   mv voitta-omemepo/src .
   mv voitta-omemepo/docs .
   mv voitta-omemepo/pyproject.toml .
   mv voitta-omemepo/README.md .
   rmdir voitta-omemepo
   ```
   **Acceptance:** `ls $HOME/g/git.voitta/.claude-plugin/marketplace.json`
   exists; `voitta-omemepo/` is gone.

2. **Fix URL refs.** Replace `voitta-ai/voitta-omemepo` → `voitta-ai/omemepo`
   in: README.md, docs/architecture.md, plugins/voitta-misc/README.md,
   plugins/voitta-misc/.claude-plugin/plugin.json,
   .claude-plugin/marketplace.json. Also: marketplace `name` field
   `"voitta-omemepo"` → `"omemepo"`.
   **Acceptance:** `grep -r "voitta-ai/voitta-omemepo" .` returns nothing.

3. **Commit and push.** Add specific paths only (NEVER `git add .` or `-A`):
   `.gitignore .claude-plugin plugins src docs pyproject.toml README.md
   .handoffs`. Commit message describes the skeleton scope. Push to
   origin/master.
   **Acceptance:** `git log --oneline` shows the new commit; remote master
   updated.

4. **Implement `pack`** (highest-value starter).
   - Include: `skills/`, `agents/`, `commands/`, `hooks/`, `CLAUDE.md`
     (dereference if symlink), `settings.json` (secrets redacted),
     `settings.local.json`, keybindings, `plugins/installed_plugins.json`
     (identifiers) or full `plugins/` — see open question below.
   - Exclude: `history.jsonl`, `sessions/`, `file-history/`, `cache/`,
     `shell-snapshots/`, `paste-cache/`, `debug/`, `stats-cache.json`,
     `statsig/`, `ide/`, `session-env/`, `*.bak`, `#*#`.
   - Secret redaction: start pattern-based (regex over token-shaped values
     in `mcpServers[*].env` and top-level auth-ish keys). Schema-based is v2.
   - Default to `--redact-secrets` ON.
   **Acceptance:** `omemepo pack -o /tmp/p.tgz` creates a tarball; extracting
   and diffing vs a fresh `~/.claude/` shows only excluded-path differences
   and redacted tokens.

5. **Implement `unpack`** (mirror of pack). Refuse to overwrite without
   `--force`. Restore excluded paths NOT (they were never in the tarball).

## Constraints

- **YAGNI.** No features beyond what's asked. No tests unless user requests.
  No error handling for impossible scenarios. No backwards-compat shims.
- **Python style** (from user's global CLAUDE.md):
  - Specific imports only; no wildcards
  - No tabs in multiline strings
  - No Unicode emoji in code (OK in markdown)
  - Never have expressions in return statements — assign to `retval` first
  - Use functional / Optional style where applicable (mostly a Java rule but
    the spirit applies)
- **Git rules:**
  - Always `git --no-pager`
  - Never `git add .` or `-A`
  - Never `--no-verify`, never `--amend` existing commits
  - User must explicitly approve commits
- **Marketplace invariant:** `plugins/` must install via stock Claude Code
  with zero omemepo code involved.
- **Secret safety:** redaction default is opt-out, never silently ship tokens.
- **Do not touch** `~/.claude/` contents during development. All dev against
  test fixtures or explicit user opt-in.

## Open Questions — for the user

- **License:** AGPL-3.0 (matches voitta-rag, llm-tldr) vs MIT (matches
  truffaldino, broader adoption). Decide before v0.1 tag.
- **Pack surface for plugins:** carry `~/.claude/plugins/` contents in the
  tarball wholesale, or carry just installed-plugin identifiers and
  re-install on unpack via `/plugin`? Re-install self-heals version drift
  but needs network; wholesale is faster and offline-capable.
- **Secret redaction:** pattern-based (regex over common token shapes) vs
  schema-based (per-MCP-server allowlist of safe fields)? Pattern-based
  ships faster; schema-based is sound by construction but needs a catalog.
- **Themed plugin split trigger:** what causes a theme to split out of
  `voitta-misc`? Number of skills, semantic cohesion, contributor request?

## References

- Voitta blog tag: https://blog.debedb.com/tag/voitta/
- Sibling projects (all under `$HOME/g/git.voitta/`): voitta-rag,
  voitta-yolt, truffaldino, jetbrains-voitta, llm-tldr, leviosa
- Real marketplace examples on this box:
  `~/.claude/plugins/marketplaces/{openai-codex,every-marketplace,claude-handoff,thedotmack}/.claude-plugin/marketplace.json`
