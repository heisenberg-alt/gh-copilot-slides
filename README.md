# Slide Builder

AI-powered presentation engine. Research any topic, generate styled decks, export to HTML / PPTX / PDF.

Built with a **5-agent orchestrator**, a **Go CLI**, and an **MCP server** for VS Code Copilot integration.

---

## Quick Start

### VS Code Copilot

```bash
pip install -e ".[all]"
```

Open in VS Code — the MCP server auto-registers via `.vscode/mcp.json`. Then in Copilot Chat:

```
@slide-builder Create a presentation about renewable energy from https://www.irena.org
```

### Go CLI

```bash
go build -o bin/slides ./cmd/slides

# Research-driven (full pipeline)
./bin/slides research --topic "AI in Healthcare" --urls "https://example.com/report" --formats html,pptx,pdf

# Interactive mode
./bin/slides research

# Quick generation
./bin/slides new --topic "Startup Pitch" --style neon_cyber --output pitch.html

# Convert PowerPoint
./bin/slides convert deck.pptx --style bold_signal --output web-deck.html

# Edit existing deck
./bin/slides edit --instruction "Change slide 3 to a quote slide"
```

### Docker

```bash
docker build -t slide-builder .
docker run -e GITHUB_TOKEN="$GITHUB_TOKEN" slide-builder
```

---

## Architecture

| Component | Stack | Role |
|-----------|-------|------|
| MCP Server | Python / FastMCP | VS Code Copilot integration, 12 tools, 3 prompts |
| Agent Team | Python | Research → Curate → Style → Export → Edit |
| CLI | Go / Cobra | Standalone TUI workflow |
| Exporters | Python | HTML, PPTX, PDF output |

### Agent Pipeline

```
Topic + URLs + Files
       │
       ▼
 ┌────────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────┐
 │  Research   │ ──▶ │  Curator   │ ──▶ │    Style     │ ──▶ │ Exporter │
 │  Agent      │     │  Agent     │     │  Recommender │     │ (H/P/PDF)│
 └────────────┘     └────────────┘     └──────────────┘     └──────────┘
                                                                  │
                                                                  ▼
                                                           ┌──────────┐
                                                           │  Editor  │
                                                           │  Agent   │ ← natural language edits
                                                           └──────────┘
```

| Agent | Responsibility |
|-------|---------------|
| **Research** | Fetches URLs, DuckDuckGo search, local files (.pdf, .docx, .pptx, .txt, .md). Synthesizes facts, stats, quotes. |
| **Curator** | Structures research into a slide narrative with proper types, density, and arc. |
| **Style Recommender** | Matches content tone to the best visual preset. Extracts themes from PPTX templates. |
| **Editor** | Post-generation editing via natural language — reorder, retype, refine. |

---

## Output Formats

| Format | Engine | Notes |
|--------|--------|-------|
| HTML | Jinja2 templates | Zero-dependency, single file, animations, keyboard/touch/swipe nav, responsive |
| PPTX | python-pptx | Styled slides, speaker notes, template-based branding |
| PDF | Playwright | Pixel-perfect render of HTML slides, one page per slide |

---

## Style Presets

10 built-in presets across dark, light, and specialty themes:

| Preset | Character |
|--------|-----------|
| Bold Signal | Confident, high-impact |
| Electric Studio | Sleek, minimal, premium |
| Creative Voltage | Energetic, retro-modern |
| Dark Botanical | Elegant, artistic |
| Notebook Tabs | Editorial, structured |
| Pastel Geometry | Friendly, approachable |
| Split Pastel | Clean, playful |
| Vintage Editorial | Witty, personality-driven |
| Neon Cyber | Futuristic, cyberpunk |
| Terminal Green | Developer, retro terminal |

```bash
./bin/slides list-styles           # list all presets
./bin/slides preview --mood calm   # generate visual previews
```

---

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `GITHUB_TOKEN` | GitHub Copilot API auth | — |
| `OPENAI_API_KEY` | OpenAI API auth | — |
| `SLIDE_LLM_PROVIDER` | Force `copilot` or `openai` | auto-detect |
| `SLIDE_LLM_MODEL` | Model override | `gpt-4o` |
| `SLIDE_LLM_TIMEOUT` | Request timeout (seconds) | `60` |

Auto-detection: prefers Copilot (`GITHUB_TOKEN`) when available, falls back to OpenAI.

---

## Sessions

Presentations persist as sessions in `.slide-sessions/`, enabling:

- Iterative editing across commands
- Style changes without regenerating content
- Re-export to additional formats
- Full edit history

---

## Development

### Requirements

- **Go 1.23+** — CLI
- **Python 3.10+** — MCP server, agents, exporters
- **GitHub Copilot** or **OpenAI API** access

### Install

```bash
# Full (all features)
pip install -e ".[all]"

# PDF export
pip install -e ".[pdf]"
python -m playwright install chromium

# Research file support (PDF/DOCX)
pip install -e ".[research]"
```

### Test

```bash
# Python
pytest

# Go
go test ./...
```

### Project Structure

```
cmd/slides/           Go CLI (Cobra)
internal/             Go internals — Copilot client, HTML generator, style loader
slide_mcp/
├── server.py         MCP server entry point
├── session.py        Session persistence
├── agents/           Research, Curator, Style, Editor, Orchestrator
├── llm/              Configurable LLM client (Copilot + OpenAI)
├── exporters/        HTML, PPTX, PDF exporters
└── styles/           Style preset management
templates/
├── base.html         Presentation template
├── preview.html      Single-slide preview
└── presets/          10 JSON style configs
```

---

## License

MIT
