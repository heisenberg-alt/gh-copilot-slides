# Slide Builder — GitHub Copilot Edition

A dual-architecture tool for creating stunning, animation-rich HTML presentations — from scratch or by converting PowerPoint files. Built with **GitHub Copilot SDK**, an **AI agent team**, and a standalone **Go CLI**.

Features a **5-agent orchestrator** that researches topics from URLs/web/files, curates content into slides, recommends styles, and exports to **HTML, PPTX, and PDF**.

## Architecture

| Component | Language | Purpose |
|-----------|----------|---------|
| **MCP Server** | Python | VS Code Copilot agent-mode integration, PPT conversion |
| **Agent Team** | Python | Research, curation, style recommendation, editing |
| **CLI** | Go | Standalone presentation creation, interactive workflow |
| **Exporters** | Python | HTML, PPTX, and PDF output |
| **Templates** | HTML/CSS/JS | Shared style presets and base templates |

```
slide-builder-ghcp/
├── cmd/slides/              # Go CLI (Cobra)
│   ├── main.go              # Root command
│   ├── new.go               # Create new presentation
│   ├── research.go          # Research-driven pipeline (NEW)
│   ├── edit.go              # Edit existing presentations (NEW)
│   ├── convert.go           # PPT → HTML conversion
│   ├── preview.go           # Generate style previews
│   └── list_styles.go       # List all presets
├── internal/
│   ├── copilot/client.go    # GitHub Copilot API client
│   ├── generator/generator.go # HTML generation engine
│   └── styles/styles.go     # Style preset loader
├── slide_mcp/
│   ├── server.py            # MCP server (FastMCP)
│   ├── generator.py         # Python HTML generator
│   ├── ppt_converter.py     # python-pptx integration
│   ├── session.py           # Session persistence (NEW)
│   ├── llm/                 # Configurable LLM client (NEW)
│   │   ├── __init__.py
│   │   └── client.py        # Copilot + OpenAI backends
│   ├── agents/              # AI Agent Team (NEW)
│   │   ├── __init__.py
│   │   ├── base.py           # Agent base class & shared context
│   │   ├── orchestrator.py   # Pipeline coordinator
│   │   ├── researcher.py     # URL/web/file content research
│   │   ├── curator.py        # Content → slide curation
│   │   ├── style_recommender.py # Style/theme selection
│   │   └── editor.py         # Post-generation editing
│   ├── exporters/            # Multi-format output (NEW)
│   │   ├── __init__.py
│   │   ├── html_exporter.py  # Wraps existing generator
│   │   ├── pptx_exporter.py  # python-pptx generation
│   │   └── pdf_exporter.py   # Playwright HTML→PDF
│   └── styles/__init__.py   # Style preset management
├── templates/
│   ├── base.html            # Full presentation template
│   ├── preview.html         # Single-slide preview template
│   └── presets/             # 10 JSON style presets
└── .vscode/mcp.json         # VS Code MCP server config
```

## Quick Start

### Option 1: VS Code Copilot (MCP Server)

1. **Install Python dependencies:**
   ```bash
   pip install -e ".[all]"
   # Or minimal: pip install -e .
   ```

2. **Open this project in VS Code** — the MCP server is auto-configured via `.vscode/mcp.json`

3. **Use in Copilot Chat (agent mode):**
   ```
   @slide-builder Create a researched presentation about renewable energy from https://www.irena.org
   ```

   Or use prompts:
   ```
   @slide-builder /research_and_present
   @slide-builder /new_presentation
   @slide-builder /convert_powerpoint
   ```

### Option 2: Go CLI

1. **Build the CLI:**
   ```bash
   go build -o bin/slides ./cmd/slides
   ```

2. **Research-driven presentation (NEW):**
   ```bash
   ./bin/slides research --topic "AI in Healthcare" --urls "https://example.com/report" --formats html,pptx,pdf
   ```

3. **Interactive research mode:**
   ```bash
   ./bin/slides research
   ```

4. **Edit an existing presentation:**
   ```bash
   ./bin/slides edit --instruction "Change slide 3 to a quote slide"
   ./bin/slides edit  # interactive edit loop
   ```

5. **Create a presentation (simple mode):**
   ```bash
   ./bin/slides new --topic "AI Startup Pitch" --style neon_cyber --output pitch.html
   ```

6. **Convert a PowerPoint:**
   ```bash
   ./bin/slides convert deck.pptx --style bold_signal --output web-deck.html
   ```

7. **Preview styles:**
   ```bash
   ./bin/slides preview --mood excited --output ./previews/
   ```

8. **List all styles:**
   ```bash
   ./bin/slides list-styles
   ```

## AI Agent Team

The orchestrator coordinates 5 specialized agents:

| Agent | Role |
|-------|------|
| **Research Agent** | Fetches content from URLs, web search (DuckDuckGo), and local files (.pdf, .docx, .pptx, .txt, .md). Synthesizes key facts, statistics, quotes, and themes. |
| **Curator Agent** | Transforms raw research into a structured slide narrative with proper slide types, information density, and narrative arc. |
| **Style Recommender** | Analyzes content tone and audience to recommend the best visual preset. Can also extract custom themes from PPTX templates. |
| **Editor Agent** | Accepts natural language edit instructions to modify slides post-generation: reorder, add/remove, change types, refine wording. |
| **Orchestrator** | Coordinates the pipeline: research → curate → style → export → edit loop. Manages session persistence. |

### Pipeline Flow

```
User Input (topic, URLs, files)
        │
        ▼
┌─────────────────┐
│ Research Agent   │ ← URLs, web search, local files
│ (gather + synth) │
└────────┬────────┘
         │ research bundle
         ▼
┌─────────────────┐
│ Curator Agent    │ ← research data, slide count, purpose
│ (structure)      │
└────────┬────────┘
         │ slides[]
         ▼
┌─────────────────┐
│ Style Recommender│ ← content tone, mood, audience
│ (recommend)      │
└────────┬────────┘
         │ style preset
         ▼
┌─────────────────┐
│ Exporters        │ → HTML, PPTX, PDF
│ (generate)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Editor Agent     │ ← natural language edits (loop)
│ (refine)         │
└─────────────────┘
```

### LLM Configuration

The agent team supports configurable LLM backends:

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | GitHub Copilot API (default) |
| `OPENAI_API_KEY` | OpenAI API |
| `SLIDE_LLM_PROVIDER` | Force provider: `"copilot"` or `"openai"` |
| `SLIDE_LLM_MODEL` | Override model (default: `gpt-4o`) |

Auto-detection: if `GITHUB_TOKEN` is set, uses Copilot; if `OPENAI_API_KEY`, uses OpenAI.

## Output Formats

| Format | Engine | Features |
|--------|--------|----------|
| **HTML** | Template engine | Zero-dependency, animations, keyboard/touch nav, responsive |
| **PPTX** | python-pptx | Styled slides with preset colors/fonts, speaker notes, from-scratch or template-based |
| **PDF** | Playwright (Chromium) | Pixel-perfect rendering of HTML slides, one page per slide |

### PPTX Templates

You can apply a PPTX template's branding to your presentation:
```bash
./bin/slides research --topic "Q4 Results" --pptx-template corporate.pptx --formats pptx
```
This extracts colors, fonts, and theme from the template and applies them to the generated slides.

## Style Presets

### Dark Themes
| Preset | Vibe |
|--------|------|
| **Bold Signal** | Confident, bold, modern, high-impact |
| **Electric Studio** | Sleek, minimal, premium, design-studio |
| **Creative Voltage** | Bold, creative, energetic, retro-modern |
| **Dark Botanical** | Elegant, sophisticated, artistic, premium |

### Light Themes
| Preset | Vibe |
|--------|------|
| **Notebook Tabs** | Editorial, structured, paper-like, professional |
| **Pastel Geometry** | Friendly, organized, modern, approachable |
| **Split Pastel** | Clean, modern, playful, balanced |
| **Vintage Editorial** | Witty, confident, editorial, personality-driven |

### Specialty
| Preset | Vibe |
|--------|------|
| **Neon Cyber** | Futuristic, techy, neon, cyberpunk |
| **Terminal Green** | Developer-focused, hacker, retro terminal |

## Mood → Style Mapping

| Mood | Recommended Styles |
|------|-------------------|
| Impressed / Confident | Bold Signal, Electric Studio, Dark Botanical |
| Excited / Energized | Creative Voltage, Neon Cyber, Split Pastel |
| Calm / Focused | Notebook Tabs, Vintage Editorial, Pastel Geometry |
| Inspired / Moved | Dark Botanical, Vintage Editorial, Pastel Geometry |
| Professional | Bold Signal, Notebook Tabs, Electric Studio |
| Playful | Creative Voltage, Split Pastel, Pastel Geometry |
| Technical | Terminal Green, Neon Cyber, Electric Studio |
| Elegant | Dark Botanical, Vintage Editorial, Notebook Tabs |

## MCP Tools Reference

### Original Tools
| Tool | Description |
|------|-------------|
| `list_styles` | List all 10 available style presets |
| `get_style_details` | Get full config for a specific preset |
| `preview_styles` | Generate 3 preview HTML files by mood |
| `create_presentation` | Generate full HTML presentation |
| `convert_ppt` | Convert .pptx to HTML |
| `summarize_ppt` | Extract and summarize PPT content |

### Agent-Powered Tools (NEW)
| Tool | Description |
|------|-------------|
| `research_topic` | Research a topic from URLs, web search, and files |
| `create_presentation_from_research` | Full orchestrated pipeline: research → curate → style → export |
| `edit_presentation` | Edit slides with natural language instructions |
| `export_presentation` | Export session to additional formats (html/pptx/pdf) |
| `apply_pptx_template` | Apply a PPTX template's theme to a session |
| `list_sessions` | List all saved presentation sessions |

## How It Works

### Research-Driven Workflow (NEW)

1. **Research** — AI agents gather content from URLs, DuckDuckGo search, and local files (PDF, DOCX, PPTX, TXT, MD)
2. **Curation** — Research is synthesized into a structured narrative with proper slide types
3. **Style Selection** — Content tone analysis → best preset recommendation
4. **Multi-format Export** — HTML + PPTX + PDF output
5. **Edit Loop** — Natural language editing: "Change slide 3 to a quote", "Add more data to slide 5"

### Classic Workflow

1. **Content Discovery** — Define topic, purpose, slide count
2. **Style Discovery** — Choose mood → see 3 visual previews → pick one
3. **Generation** — Content + style → single self-contained HTML file
4. **Navigation** — Arrow keys, scroll, swipe, dots — all built in

### Output Features

Every generated HTML presentation includes:
- **Zero dependencies** — single HTML file, inline CSS/JS
- **Keyboard navigation** — arrow keys, space, home/end
- **Touch/swipe** — mobile-friendly
- **Mouse wheel** — smooth scroll-snap
- **Progress bar** — visual position indicator
- **Navigation dots** — click to jump
- **Scroll-triggered animations** — fade, scale, blur variants
- **Responsive design** — viewport-fitting with `clamp()` throughout
- **Reduced motion** — respects `prefers-reduced-motion`

### Session Persistence

Presentations are saved as sessions in `.slide-sessions/`, enabling:
- Iterative editing across multiple commands
- Style changes without regenerating content
- Re-export to new formats at any time
- Full edit history tracking

### GitHub Copilot Integration

The Go CLI uses the GitHub Copilot Chat Completions API to:
- Generate slide content from a topic description
- Suggest style presets based on context
- Refine and structure user-provided content

Set `GITHUB_TOKEN` environment variable for authentication.

## Requirements

- **Go 1.22+** for the CLI
- **Python 3.10+** for the MCP server, agents, and exporters
- **python-pptx** for PowerPoint conversion and PPTX export
- **GitHub Copilot** or **OpenAI API** access for AI-powered features

### Optional Dependencies

```bash
# Full install (all features)
pip install -e ".[all]"

# PDF export only
pip install -e ".[pdf]"
python -m playwright install chromium

# Research file support (PDF/DOCX reading)
pip install -e ".[research]"
```

## License

MIT
