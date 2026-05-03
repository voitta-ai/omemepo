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

## Open questions

- **License**: AGPL-3.0 (matches voitta-rag, llm-tldr) vs MIT (matches
  truffaldino, broader adoption).
- **Plugin surface in pack**: should `~/.claude/plugins/` (installed
  marketplaces + plugins) be carried in the pack tarball, or should pack
  carry only identifiers and unpack re-install via `/plugin`? Re-install
  is smaller and self-heals version drift; direct copy is faster and works
  offline.
- **Secret redaction**: pattern-based (regex over common token shapes) vs
  schema-based (per-MCP-server allowlist of safe fields).
- **Themed plugins split**: what triggers a theme to split out of
  `voitta-misc` — number of skills, semantic cohesion, contributor request?

## Future: Claude Desktop and other tools

Claude Code is the sole first-class target. Adding Claude Desktop and
broader AI-tool support (Cline, Cursor, IntelliJ) is filed as a nice-to-
have but explicitly out of scope for v1. Truffaldino already covers those
for MCP+prompts; if omemepo grows there, it will be by composition, not
replacement.
