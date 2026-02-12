package generator

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestBuildSlideHTML(t *testing.T) {
	tests := []struct {
		name     string
		slide    Slide
		contains []string
		absent   []string
	}{
		{
			name:     "title slide",
			slide:    Slide{Type: "title", Title: "Hello", Subtitle: "World"},
			contains: []string{"title-slide", "Hello", "World", "subtitle"},
		},
		{
			name: "content slide with bullets",
			slide: Slide{
				Type:    "content",
				Title:   "Points",
				Bullets: []string{"A", "B", "C"},
			},
			contains: []string{"content-slide", "Points", "<li", "A", "B", "C"},
		},
		{
			name: "quote slide",
			slide: Slide{
				Type:        "quote",
				Title:       "Quote",
				Quote:       "Be bold",
				Attribution: "Author",
			},
			contains: []string{"quote-slide", "Be bold", "Author"},
		},
		{
			name: "code slide",
			slide: Slide{
				Type:  "code",
				Title: "Code Example",
				Code:  "fmt.Println()",
			},
			contains: []string{"code-slide", "Code Example", "fmt.Println()"},
		},
		{
			name: "feature grid slide",
			slide: Slide{
				Type:  "feature_grid",
				Title: "Features",
				Cards: []Card{
					{Title: "Fast", Description: "Very fast", Icon: "zap"},
					{Title: "Safe", Description: "Very safe"},
				},
			},
			contains: []string{"feature_grid-slide", "Features", "Fast", "Safe"},
		},
		{
			name: "image slide",
			slide: Slide{
				Type:     "image",
				Title:    "Photo",
				ImageSrc: "photo.png",
			},
			contains: []string{"image-slide", "Photo", "photo.png"},
		},
		{
			name:     "closing slide",
			slide:    Slide{Type: "closing", Title: "Thanks", Subtitle: "Goodbye"},
			contains: []string{"closing-slide", "Thanks", "Goodbye"},
		},
		{
			name:     "title without subtitle",
			slide:    Slide{Type: "title", Title: "Solo Title"},
			contains: []string{"title-slide", "Solo Title"},
			absent:   []string{"subtitle"},
		},
		{
			name: "content with subtitle no bullets",
			slide: Slide{
				Type:     "content",
				Title:    "Sub Only",
				Subtitle: "A description",
			},
			contains: []string{"content-slide", "A description"},
			absent:   []string{"<li"},
		},
		{
			name: "cards capped at 6",
			slide: Slide{
				Type:  "feature_grid",
				Title: "Grid",
				Cards: []Card{
					{Title: "C0"}, {Title: "C1"}, {Title: "C2"},
					{Title: "C3"}, {Title: "C4"}, {Title: "C5"},
					{Title: "C6"}, {Title: "C7"},
				},
			},
			absent: []string{"C6", "C7"},
		},
		{
			name: "bullets capped at 6",
			slide: Slide{
				Type:    "content",
				Title:   "Many",
				Bullets: []string{"B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7"},
			},
			absent: []string{"B6", "B7"},
		},
		// XSS prevention tests
		{
			name:     "XSS in title is escaped",
			slide:    Slide{Type: "title", Title: `<script>alert("xss")</script>`, Subtitle: `<img onerror=alert(1) src=x>`},
			contains: []string{"&lt;script&gt;", "&lt;img onerror=alert(1)"},
			absent:   []string{`<script>alert`, `<img onerror`},
		},
		{
			name:     "XSS in quote is escaped",
			slide:    Slide{Type: "quote", Quote: `<script>alert(1)</script>`, Attribution: `<b>evil</b>`},
			contains: []string{"&lt;script&gt;", "&lt;b&gt;evil&lt;/b&gt;"},
			absent:   []string{`<script>alert`, `<b>evil</b>`},
		},
		{
			name:     "XSS in bullets is escaped",
			slide:    Slide{Type: "content", Title: "Safe", Bullets: []string{`<script>xss</script>`, `normal`}},
			contains: []string{"&lt;script&gt;xss&lt;/script&gt;", "normal"},
			absent:   []string{`<script>xss</script>`},
		},
		{
			name: "XSS in cards is escaped",
			slide: Slide{
				Type:  "feature_grid",
				Title: "Grid",
				Cards: []Card{{Title: `<img src=x>`, Description: `<script>x</script>`, Icon: `<b>!!</b>`}},
			},
			contains: []string{"&lt;img src=x&gt;", "&lt;script&gt;x&lt;/script&gt;", "&lt;b&gt;!!&lt;/b&gt;"},
			absent:   []string{`<img src=x>`, `<script>x</script>`, `<b>!!</b>`},
		},
		{
			name:     "XSS in image src is escaped",
			slide:    Slide{Type: "image", Title: "Img", ImageSrc: `javascript:alert(1)`},
			contains: []string{"javascript:alert(1)"},
		},
		{
			name:     "XSS in code is escaped",
			slide:    Slide{Type: "code", Title: "Code", Code: `<script>alert(1)</script>`},
			contains: []string{"&lt;script&gt;alert(1)&lt;/script&gt;"},
			absent:   []string{`<script>alert(1)</script>`},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			html := buildSlideHTML(tc.slide)
			for _, want := range tc.contains {
				if !strings.Contains(html, want) {
					t.Errorf("expected HTML to contain %q, got:\n%s", want, html)
				}
			}
			for _, no := range tc.absent {
				if strings.Contains(html, no) {
					t.Errorf("expected HTML NOT to contain %q, got:\n%s", no, html)
				}
			}
		})
	}
}

func TestGeneratePresentation(t *testing.T) {
	tmpDir := t.TempDir()
	outPath := filepath.Join(tmpDir, "test-deck.html")

	slides := []Slide{
		{Type: "title", Title: "Test Deck", Subtitle: "Unit Test"},
		{Type: "content", Title: "Agenda", Bullets: []string{"Item 1", "Item 2"}},
		{Type: "closing", Title: "End"},
	}

	err := GeneratePresentation("Test Deck", slides, "bold_signal", outPath)
	if err != nil {
		t.Fatalf("GeneratePresentation failed: %v", err)
	}

	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("can't read output: %v", err)
	}
	content := string(data)

	for _, want := range []string{"<html", "Test Deck", "Agenda", "Item 1"} {
		if !strings.Contains(content, want) {
			t.Errorf("output missing %q", want)
		}
	}
}

func TestGeneratePresentationInvalidPreset(t *testing.T) {
	tmpDir := t.TempDir()
	outPath := filepath.Join(tmpDir, "x.html")
	err := GeneratePresentation("Bad", nil, "nonexistent_xyz", outPath)
	if err == nil {
		t.Error("expected error for invalid preset")
	}
}

func TestGeneratePreview(t *testing.T) {
	tmpDir := t.TempDir()
	outPath := filepath.Join(tmpDir, "preview.html")

	err := GeneratePreview("bold_signal", outPath, "Preview Title", "Preview Sub")
	if err != nil {
		t.Fatalf("GeneratePreview failed: %v", err)
	}

	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("can't read output: %v", err)
	}
	content := string(data)

	for _, want := range []string{"Bold Signal", "Preview Title", "Preview Sub"} {
		if !strings.Contains(content, want) {
			t.Errorf("preview output missing %q", want)
		}
	}
}
