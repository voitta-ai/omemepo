# omemepo — maintainer instructions

This file is read by Claude Code sessions working in this repo.

## Repo invariants

- The `plugins/` tree must install via stock Claude Code with zero `src/`
  code involved. Tool is additive; marketplace stands alone.
- `.claude-plugin/marketplace.json` lives at repo root (not under
  `plugins/`).
- Marketplace name field: `omemepo` (not `voitta-omemepo`).
- GitHub remote: `voitta-ai/omemepo` (not `voitta-ai/voitta-omemepo`).

## Themed plugin split — when to suggest it

Skills land in `plugins/voitta-misc/` by default. When reviewing skill
additions, watch for these signals that a theme has emerged and a split
into a new themed plugin (`voitta-aws`, `voitta-git`, `voitta-debug`,
`voitta-infra`, etc.) is warranted:

- A cluster of skills shares a clear domain (AWS service ops, git
  workflow, debugging tooling, infra/terraform).
- Skills share dependencies, MCP servers, or environment that wouldn't
  apply to other voitta-misc users.
- A target subset of users would install the theme but not voitta-misc as
  a whole, or vice versa.
- A contributor explicitly proposes a theme.

When two or more signals fire, propose a split: file an issue, draft the
new plugin directory under `plugins/<theme>/`, move the skills, register
the plugin in `.claude-plugin/marketplace.json`. Do NOT split mechanically
on a skill-count threshold.

## Coding rules (apply to `src/omemepo/`)

- Python 3.11+, typer for CLI.
- Specific imports only; never wildcard imports.
- No tabs in multiline strings.
- No Unicode emoji in code (OK in markdown).
- Never have an expression in a `return` statement; assign to a local
  first, then return the local.
- YAGNI. No tests unless the user requests them. No error handling for
  impossible scenarios. No backwards-compat shims.

## Git rules

- Always `git --no-pager`.
- Never `git add .` or `-A`. Stage specific paths.
- Never `--no-verify`, never `--amend` an existing commit.
- User must explicitly approve commits.

## Secret safety

`omemepo pack` MUST redact secrets by default. The redaction model is a
**blacklist of key-name patterns** (substring, case-insensitive):
`token`, `secret`, `password`, `passwd` seed the list. Users can add and
remove entries via config. Do not silently ship unredacted MCP tokens
under any circumstance.

## Don't touch the user's `~/.claude/`

All development against test fixtures or explicit user opt-in. Never
mutate the live `~/.claude/` tree from omemepo dev/test code paths.
