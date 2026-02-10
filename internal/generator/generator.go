// Package generator creates HTML presentations from structured content
// and style presets. It renders the shared base.html template with the
// chosen preset's colors, fonts, and CSS.
package generator

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/sameerankalgi/slide-builder-ghcp/internal/styles"
)

// Slide represents a single slide's content.
type Slide struct {
	Type        string            `json:"type"` // title, content, feature_grid, code, quote, image, closing
	Title       string            `json:"title"`
	Subtitle    string            `json:"subtitle,omitempty"`
	Bullets     []string          `json:"bullets,omitempty"`
	Code        string            `json:"code,omitempty"`
	Quote       string            `json:"quote,omitempty"`
	Attribution string            `json:"attribution,omitempty"`
	Cards       []Card            `json:"cards,omitempty"`
	ImageSrc    string            `json:"image_src,omitempty"`
}

// Card is a feature card in a grid slide.
type Card struct {
	Title       string `json:"title"`
	Description string `json:"description"`
	Icon        string `json:"icon,omitempty"`
}

// templatesDir finds the templates directory from the working directory.
func templatesDir() (string, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	candidates := []string{
		filepath.Join(cwd, "templates"),
		filepath.Join(cwd, "..", "templates"),
		filepath.Join(cwd, "..", "..", "templates"),
	}
	ex, _ := os.Executable()
	if ex != "" {
		exDir := filepath.Dir(ex)
		candidates = append(candidates,
			filepath.Join(exDir, "templates"),
			filepath.Join(exDir, "..", "templates"),
		)
	}
	for _, c := range candidates {
		if info, err := os.Stat(c); err == nil && info.IsDir() {
			return c, nil
		}
	}
	return "", fmt.Errorf("templates directory not found")
}

// buildSlideHTML renders a single slide to HTML.
func buildSlideHTML(s Slide) string {
	switch s.Type {
	case "title":
		sub := ""
		if s.Subtitle != "" {
			sub = fmt.Sprintf(`<p class="reveal subtitle">%s</p>`, s.Subtitle)
		}
		return fmt.Sprintf(`
    <section class="slide title-slide">
        <div class="slide-content" style="align-items: center; text-align: center;">
            <h1 class="reveal">%s</h1>
            %s
        </div>
    </section>`, s.Title, sub)

	case "quote":
		attr := ""
		if s.Attribution != "" {
			attr = fmt.Sprintf(`<p class="reveal" style="margin-top: 1rem; color: var(--text-secondary);">— %s</p>`, s.Attribution)
		}
		return fmt.Sprintf(`
    <section class="slide quote-slide">
        <div class="slide-content" style="align-items: center; text-align: center;">
            <blockquote class="reveal" style="font-family: var(--font-display); font-size: var(--h2-size); font-style: italic; max-width: 800px;">
                &ldquo;%s&rdquo;
            </blockquote>
            %s
        </div>
    </section>`, s.Quote, attr)

	case "code":
		return fmt.Sprintf(`
    <section class="slide code-slide">
        <div class="slide-content">
            <h2 class="reveal">%s</h2>
            <pre class="reveal" style="background: rgba(0,0,0,0.3); padding: clamp(1rem, 2vw, 2rem); border-radius: 8px; overflow: hidden; font-family: 'JetBrains Mono', monospace; font-size: var(--small-size); line-height: 1.6; margin-top: var(--content-gap);"><code>%s</code></pre>
        </div>
    </section>`, s.Title, s.Code)

	case "feature_grid":
		var cards strings.Builder
		for i, c := range s.Cards {
			if i >= 6 {
				break
			}
			icon := ""
			if c.Icon != "" {
				icon = fmt.Sprintf(`<div style="font-size: 1.5em; margin-bottom: 0.5rem;">%s</div>`, c.Icon)
			}
			cards.WriteString(fmt.Sprintf(`
                <div class="card reveal" style="background: rgba(255,255,255,0.05); padding: clamp(1rem, 2vw, 1.5rem); border-radius: 12px;">
                    %s
                    <h3 style="font-size: var(--body-size); font-weight: 600; margin-bottom: 0.5rem;">%s</h3>
                    <p style="font-size: var(--small-size); color: var(--text-secondary);">%s</p>
                </div>`, icon, c.Title, c.Description))
		}
		return fmt.Sprintf(`
    <section class="slide feature_grid-slide">
        <div class="slide-content">
            <h2 class="reveal">%s</h2>
            <div class="grid" style="margin-top: var(--content-gap);">%s
            </div>
        </div>
    </section>`, s.Title, cards.String())

	case "image":
		return fmt.Sprintf(`
    <section class="slide image-slide">
        <div class="slide-content" style="align-items: center;">
            <h2 class="reveal">%s</h2>
            <img class="reveal" src="%s" alt="%s" style="margin-top: var(--content-gap); border-radius: 8px;">
        </div>
    </section>`, s.Title, s.ImageSrc, s.Title)

	case "closing":
		sub := ""
		if s.Subtitle != "" {
			sub = fmt.Sprintf(`<p class="reveal subtitle" style="margin-top: var(--content-gap);">%s</p>`, s.Subtitle)
		}
		return fmt.Sprintf(`
    <section class="slide closing-slide">
        <div class="slide-content" style="align-items: center; text-align: center;">
            <h1 class="reveal">%s</h1>
            %s
        </div>
    </section>`, s.Title, sub)

	default: // content
		var body strings.Builder
		if len(s.Bullets) > 0 {
			body.WriteString(`
            <ul class="bullet-list" style="margin-top: var(--content-gap); list-style: none; padding: 0; display: flex; flex-direction: column; gap: var(--element-gap);">`)
			for i, b := range s.Bullets {
				if i >= 6 {
					break
				}
				body.WriteString(fmt.Sprintf(`
                <li class="reveal">%s</li>`, b))
			}
			body.WriteString(`
            </ul>`)
		} else if s.Subtitle != "" {
			body.WriteString(fmt.Sprintf(`
            <p class="reveal" style="margin-top: var(--content-gap); color: var(--text-secondary);">%s</p>`, s.Subtitle))
		}
		return fmt.Sprintf(`
    <section class="slide content-slide">
        <div class="slide-content">
            <h2 class="reveal">%s</h2>%s
        </div>
    </section>`, s.Title, body.String())
	}
}

// GeneratePresentation creates a complete HTML file from slides and a preset.
func GeneratePresentation(title string, slides []Slide, styleName string, outputPath string) error {
	preset, err := styles.LoadPreset(styleName)
	if err != nil {
		return fmt.Errorf("loading preset: %w", err)
	}

	tDir, err := templatesDir()
	if err != nil {
		return fmt.Errorf("finding templates: %w", err)
	}

	tmplBytes, err := os.ReadFile(filepath.Join(tDir, "base.html"))
	if err != nil {
		return fmt.Errorf("reading base template: %w", err)
	}
	tmpl := string(tmplBytes)

	// Build all slide HTML
	var allSlides strings.Builder
	for _, s := range slides {
		allSlides.WriteString(buildSlideHTML(s))
	}

	// Replace template variables
	replacements := map[string]string{
		"{{ title }}":               title,
		"{{ font_import }}":         preset.FontImport,
		"{{ extra_css }}":           preset.ExtraCSS,
		"{{ slides_html }}":         allSlides.String(),
		"{{ fonts.display.family }}": preset.Fonts["display"].Family,
		"{{ fonts.body.family }}":    preset.Fonts["body"].Family,
	}

	for k, v := range preset.Colors {
		replacements[fmt.Sprintf("{{ colors.%s }}", k)] = v
	}

	for old, new := range replacements {
		tmpl = strings.ReplaceAll(tmpl, old, new)
	}

	// Ensure output directory exists
	if err := os.MkdirAll(filepath.Dir(outputPath), 0o755); err != nil {
		return fmt.Errorf("creating output dir: %w", err)
	}

	if err := os.WriteFile(outputPath, []byte(tmpl), 0o644); err != nil {
		return fmt.Errorf("writing file: %w", err)
	}

	return nil
}

// GeneratePreview creates a single-slide style preview HTML file.
func GeneratePreview(styleName, outputPath, previewTitle, previewSubtitle string) error {
	preset, err := styles.LoadPreset(styleName)
	if err != nil {
		return fmt.Errorf("loading preset: %w", err)
	}

	tDir, err := templatesDir()
	if err != nil {
		return fmt.Errorf("finding templates: %w", err)
	}

	tmplBytes, err := os.ReadFile(filepath.Join(tDir, "preview.html"))
	if err != nil {
		return fmt.Errorf("reading preview template: %w", err)
	}
	tmpl := string(tmplBytes)

	// Build color swatches
	var swatches strings.Builder
	for key, value := range preset.Colors {
		if !strings.HasPrefix(value, "linear-gradient") && !strings.HasPrefix(value, "rgba") {
			swatches.WriteString(fmt.Sprintf(
				`<div class="swatch" style="background: %s;" title="%s"></div>`+"\n        ",
				value, key,
			))
		}
	}

	replacements := map[string]string{
		"{{ preset_name }}":          preset.DisplayName,
		"{{ font_import }}":          preset.FontImport,
		"{{ extra_css }}":            preset.ExtraCSS,
		"{{ preview_title }}":        previewTitle,
		"{{ preview_subtitle }}":     previewSubtitle,
		"{{ color_swatches }}":       swatches.String(),
		"{{ fonts.display.family }}": preset.Fonts["display"].Family,
		"{{ fonts.body.family }}":    preset.Fonts["body"].Family,
	}
	for k, v := range preset.Colors {
		replacements[fmt.Sprintf("{{ colors.%s }}", k)] = v
	}

	for old, new := range replacements {
		tmpl = strings.ReplaceAll(tmpl, old, new)
	}

	if err := os.MkdirAll(filepath.Dir(outputPath), 0o755); err != nil {
		return fmt.Errorf("creating output dir: %w", err)
	}
	return os.WriteFile(outputPath, []byte(tmpl), 0o644)
}
