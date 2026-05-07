# omemepo architecture

## What this is

A portability and sharing layer for Claude Code, combining:

1. A CLI/MCP tool for packing, unpacking, publishing, diffing, and syncing
   your personal Claude Code profile.
2. A curated Claude Code marketplace maintained by Voitta.

Both live in this single repo but are independent:

- The marketplace is consumable without the tool:
  `/plugin marketplace add voitta-ai/voitta-omemepo` works with stock
  Claude Code.
- The tool is usable without the marketplace: `omemepo pack`/`unpack` never
  touch any marketplace.

## Design decisions

### Combined repo (tool + marketplace)

A single repo hosts both.

Rationale:
- Branding unity: the "what does omemepo mean?" answer and the "what's the
  Voitta marketplace?" answer are intertwined.
- Contribution unity: Voitta projects contribute plugins here; tool bugs
  filed here.
- No extra discoverability friction: one URL to remember.

Invariant preserved: the `plugins/` tree must never require code in `src/`
to install. Omemepo is additive on top of the native `/plugin install`
flow.

### Marketplace layout: themed plugins

Not per-skill (too noisy), not one mega plugin (can't opt out). Planned
themes: `voitta-aws`, `voitta-git`, `voitta-debug`, `voitta-infra`, plus a
`voitta-misc` catch-all.

Currently only `voitta-misc` is registered; themes split off as content
accumulates.

### Other Voitta projects as plugins

Existing Voitta services that expose MCP can ship plugins here to provide
the Claude Code-side glue (MCP wiring + usage skills) without the plugin
owning the service lifecycle:

- voitta-rag — MCP for self-hosted RAG
- voitta-yolt — Claude Code safety hook
- jetbrains-voitta — IntelliJ MCP bridge
- llm-tldr — code-structure MCP
- truffaldino — cross-tool config sync MCP (the Claude Code slice may move
  entirely into `omemepo mcp`)

### Language: Python 3.11+

Rationale:
- Stack fit with voitta-rag and truffaldino
- Direct code reuse from truffaldino (omemepo subsumes its Claude Code
  scope)
- Mature MCP SDK
- Familiar to all Voitta contributors

Distribution via `pipx install omemepo` or `uv tool install omemepo`.
Single-binary fallback via shiv/pex if needed later.

### CLI framework: typer

Type hints double as self-documenting command surface.

### Publish model

- Outside contributors: PR-reviewed
- Listed maintainers: direct push
- `CODEOWNERS` per plugin directory so plugin authors own their plugin
  without owning the whole repo
- Branch protection on `main`, required review from CODEOWNERS, squash
  merges

## Commands (planned)

| Command | Status | Purpose |
|---|---|---|
| `omemepo pack` | stub | Tar up `~/.claude/`, redact secrets |
| `omemepo unpack` | stub | Restore a profile tarball |
| `omemepo publish <path>` | stub | Open PR promoting a local artifact |
| `omemepo diff` | stub | Local vs marketplace delta |
| `omemepo mcp ...` | stub | MCP/prompt sync (Claude Code scope) |
| `omemepo version` | works | Print version |

## What's not in the skeleton

- Actual pack/unpack implementation
- Secret detection/redaction rules
- MCP sync logic
- MCP server (omemepo exposing its own tools via MCP)
- Themed plugins beyond `voitta-misc`
- `CODEOWNERS`
- CI
- `LICENSE`

## Resolved questions

### License: MIT

Matches truffaldino. Broader adoption than AGPL. Tooling vs service shapes
that decision differently from voitta-rag/llm-tldr.

### Plugin surface in pack: hybrid, identifiers default

`omemepo pack` defaults to carrying only installed-plugin identifiers
(marketplace + name + version). On `unpack`, omemepo re-installs each
entry via `/plugin` flows. Self-heals version drift, keeps tarball small.

Flag `--include-plugin-contents` switches to wholesale: tar the entire
`~/.claude/plugins/` tree byte-for-byte. For air-gap migration, local
forks, or reproducing exact state.

### Secret redaction: schema-based blacklist (not allowlist)

Default-allow. The redactor walks structured config (settings.json, MCP
configs) and redacts keys whose names match a blacklist of patterns.

Seed blacklist patterns (case-insensitive substring match on key names):
`token`, `secret`, `password`, `passwd`. Users can REMOVE entries from the
blacklist (e.g. a project legitimately uses a `passwordHashAlgorithm` key
that's not actually a secret) and ADD entries.

Why blacklist not allowlist: allowlist requires per-MCP-server schema
catalogs that don't exist yet; new servers fail closed and break for
users until catalog catches up. Blacklist ships today and stays correct
across new MCP servers without maintenance, at the cost of missing novel
secret-shaped fields whose key names don't match the blacklist.

### Themed plugin split: semantic cohesion (maintainer judgment)

Skills live in `voitta-misc` until a coherent theme emerges
(`voitta-aws`, `voitta-git`, `voitta-debug`, …). Maintainer proposes split.
No mechanical skill-count threshold.

The repo's `CLAUDE.md` carries operating instructions for the maintainer
to recognize when a split is warranted: a cluster of skills that share a
domain, common dependencies, or a target subset of users.

## Future: Claude Desktop and other tools

Claude Code is the sole first-class target. Adding Claude Desktop and
broader AI-tool support (Cline, Cursor, IntelliJ) is filed as a nice-to-
have but explicitly out of scope for v1. Truffaldino already covers those
for MCP+prompts; if omemepo grows there, it will be by composition, not
replacement.
