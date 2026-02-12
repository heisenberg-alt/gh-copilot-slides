# Slide Builder — GitHub Copilot Edition

A dual-architecture tool for creating stunning, animation-rich HTML presentations — from scratch or by converting PowerPoint files. Built with **GitHub Copilot SDK** and as a standalone **Go CLI**.

## Architecture

| Component | Language | Purpose |
|-----------|----------|---------|
| **MCP Server** | Python | VS Code Copilot agent-mode integration, PPT conversion |
| **CLI** | Go | Standalone presentation creation, interactive workflow |
| **Templates** | HTML/CSS/JS | Shared style presets and base templates |

```
slide-builder-ghcp/
├── cmd/slides/              # Go CLI (Cobra)
│   ├── main.go              # Root command
│   ├── new.go               # Create new presentation
│   ├── convert.go           # PPT → HTML conversion
│   ├── preview.go           # Generate style previews
│   └── list_styles.go       # List all presets
├── internal/
│   ├── copilot/client.go    # GitHub Copilot API client
│   ├── generator/generator.go # HTML generation engine
│   └── styles/styles.go     # Style preset loader
├── mcp/
│   ├── server.py            # MCP server (FastMCP)
│   ├── generator.py         # Python HTML generator
│   ├── ppt_converter.py     # python-pptx integration
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
   pip install "mcp[cli]>=1.2.0" python-pptx jinja2 pydantic
   ```

2. **Open this project in VS Code** — the MCP server is auto-configured via `.vscode/mcp.json`

3. **Use in Copilot Chat (agent mode):**
   ```
   @slide-builder Create a pitch deck about renewable energy with 10 slides
   ```

   Or use prompts:
   ```
   @slide-builder /new_presentation
   @slide-builder /convert_powerpoint
   ```

### Option 2: Go CLI

1. **Build the CLI:**
   ```bash
   go build -o bin/slides ./cmd/slides
   ```

2. **Create a presentation (interactive):**
   ```bash
   ./bin/slides new
   ```

3. **Create with flags:**
   ```bash
   ./bin/slides new --topic "AI Startup Pitch" --style neon_cyber --output pitch.html
   ```

4. **Convert a PowerPoint:**
   ```bash
   ./bin/slides convert deck.pptx --style bold_signal --output web-deck.html
   ```

5. **Preview styles:**
   ```bash
   ./bin/slides preview --mood excited --output ./previews/
   ```

6. **List all styles:**
   ```bash
   ./bin/slides list-styles
   ```

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

| Tool | Description |
|------|-------------|
| `list_styles` | List all 10 available style presets |
| `get_style_details` | Get full config for a specific preset |
| `preview_styles` | Generate 3 preview HTML files by mood |
| `create_presentation` | Generate full HTML presentation |
| `convert_ppt` | Convert .pptx to HTML |
| `summarize_ppt` | Extract and summarize PPT content |

## How It Works

### Presentation Workflow

1. **Content Discovery** — Define topic, purpose, slide count
2. **Style Discovery** — Choose mood → see 3 visual previews → pick one
3. **Generation** — Content + style → single self-contained HTML file
4. **Navigation** — Arrow keys, scroll, swipe, dots — all built in

### Output Features

Every generated presentation includes:
- **Zero dependencies** — single HTML file, inline CSS/JS
- **Keyboard navigation** — arrow keys, space, home/end
- **Touch/swipe** — mobile-friendly
- **Mouse wheel** — smooth scroll-snap
- **Progress bar** — visual position indicator
- **Navigation dots** — click to jump
- **Scroll-triggered animations** — fade, scale, blur variants
- **Responsive design** — viewport-fitting with `clamp()` throughout
- **Reduced motion** — respects `prefers-reduced-motion`

### GitHub Copilot Integration

The Go CLI uses the GitHub Copilot Chat Completions API to:
- Generate slide content from a topic description
- Suggest style presets based on context
- Refine and structure user-provided content

Set `GITHUB_TOKEN` environment variable for authentication.

## Requirements

- **Go 1.22+** for the CLI
- **Python 3.10+** for the MCP server and PPT conversion
- **python-pptx** for PowerPoint conversion
- **GitHub Copilot** access for AI-powered content generation (optional — works without it using sample content)

## License

MIT
