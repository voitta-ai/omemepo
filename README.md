# omemepo

*Omnia mea mecum porto* — "all that is mine, I carry with me."

A portability and sharing layer for Claude Code.

## Two things, one repo

1. **Personal portability.** Pack up your entire `~/.claude/` (skills, agents,
   commands, hooks, MCP configs, prompts, keybindings) and unpack it on another
   box. Secrets redacted, ephemera excluded.
2. **Shared marketplace.** A curated Claude Code marketplace of plugins
   maintained by [Voitta](https://github.com/voitta-ai).

Either is first-class. Neither requires the other.

## Use case 1: I got a new laptop

```bash
# On the old box:
omemepo pack --redact-secrets -o profile.tar.gz

# On the new box:
omemepo unpack profile.tar.gz
```

Your `~/.claude/` — including local skills, agents, commands, hooks, and
(with re-provisioned secrets) MCP configs — lands on the new machine.

## Use case 2: I want shared Voitta skills

No omemepo required. Works with stock Claude Code:

```
/plugin marketplace add voitta-ai/voitta-omemepo
/plugin install voitta-misc
```

## Install the tool

```bash
pipx install omemepo
# or
uv tool install omemepo
```

## Commands

| Command | What it does |
|---|---|
| `omemepo pack` | Tar up your `~/.claude/` profile |
| `omemepo unpack` | Restore a profile tarball |
| `omemepo publish <path>` | Open a PR promoting a local artifact to a marketplace |
| `omemepo diff` | Show local `~/.claude/` vs marketplace delta |
| `omemepo mcp ...` | Sync MCP servers and prompts (subsumes truffaldino for Claude Code) |
| `omemepo version` | Print version |

See `docs/architecture.md` for the design.

## Related Voitta projects

- [voitta-rag](https://github.com/voitta-ai/voitta-rag) — self-hosted RAG exposed via MCP
- [voitta-yolt](https://github.com/voitta-ai/voitta-yolt) — Claude Code safety hook
- [truffaldino](https://github.com/voitta-ai/truffaldino) — cross-tool AI config sync
- [jetbrains-voitta](https://github.com/voitta-ai/jetbrains-voitta) — IntelliJ MCP bridge
- [llm-tldr](https://github.com/voitta-ai/llm-tldr) — code-structure compression for LLMs

Each of these can ship an entry under `plugins/` to provide the Claude Code-side
glue (MCP wiring + usage skills).

## Status

Early skeleton. Commands are stubs. See `docs/architecture.md`.
