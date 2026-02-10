// Package styles loads and manages style presets from the shared
// templates/presets directory. Presets are JSON files defining colors,
// fonts, and CSS for each visual theme.
package styles

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// FontConfig describes a font family and its weights.
type FontConfig struct {
	Family  string `json:"family"`
	Weights []int  `json:"weights"`
	Source  string `json:"source"`
}

// Preset holds the full configuration for a single style preset.
type Preset struct {
	Name              string            `json:"name"`
	DisplayName       string            `json:"display_name"`
	Category          string            `json:"category"`
	Vibe              string            `json:"vibe"`
	Description       string            `json:"description"`
	Fonts             map[string]FontConfig `json:"fonts"`
	Colors            map[string]string `json:"colors"`
	SignatureElements []string          `json:"signature_elements"`
	FontImport        string            `json:"font_import"`
	ExtraCSS          string            `json:"extra_css"`
}

// AllPresetNames is the ordered list of all available preset names.
var AllPresetNames = []string{
	"bold_signal",
	"electric_studio",
	"creative_voltage",
	"dark_botanical",
	"notebook_tabs",
	"pastel_geometry",
	"split_pastel",
	"vintage_editorial",
	"neon_cyber",
	"terminal_green",
}

// MoodMap maps mood keywords to their recommended preset names.
var MoodMap = map[string][]string{
	"impressed":    {"bold_signal", "electric_studio", "dark_botanical"},
	"confident":    {"bold_signal", "electric_studio", "dark_botanical"},
	"excited":      {"creative_voltage", "neon_cyber", "split_pastel"},
	"energized":    {"creative_voltage", "neon_cyber", "split_pastel"},
	"calm":         {"notebook_tabs", "vintage_editorial", "pastel_geometry"},
	"focused":      {"notebook_tabs", "vintage_editorial", "pastel_geometry"},
	"inspired":     {"dark_botanical", "vintage_editorial", "pastel_geometry"},
	"moved":        {"dark_botanical", "vintage_editorial", "pastel_geometry"},
	"professional": {"bold_signal", "notebook_tabs", "electric_studio"},
	"playful":      {"creative_voltage", "split_pastel", "pastel_geometry"},
	"technical":    {"terminal_green", "neon_cyber", "electric_studio"},
	"elegant":      {"dark_botanical", "vintage_editorial", "notebook_tabs"},
}

// presetsDir returns the absolute path to the presets directory.
// It walks up from the executable / working directory to find the templates folder.
func presetsDir() (string, error) {
	// Try relative to working directory first
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}

	candidates := []string{
		filepath.Join(cwd, "templates", "presets"),
		filepath.Join(cwd, "..", "templates", "presets"),
		filepath.Join(cwd, "..", "..", "templates", "presets"),
	}

	// Also try relative to executable
	ex, err := os.Executable()
	if err == nil {
		exDir := filepath.Dir(ex)
		candidates = append(candidates,
			filepath.Join(exDir, "templates", "presets"),
			filepath.Join(exDir, "..", "templates", "presets"),
		)
	}

	for _, c := range candidates {
		if info, err := os.Stat(c); err == nil && info.IsDir() {
			return c, nil
		}
	}
	return "", fmt.Errorf("templates/presets directory not found (searched from %s)", cwd)
}

// LoadPreset reads and parses a single preset JSON file by name.
func LoadPreset(name string) (*Preset, error) {
	dir, err := presetsDir()
	if err != nil {
		return nil, err
	}
	path := filepath.Join(dir, name+".json")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("preset %q not found: %w", name, err)
	}
	var p Preset
	if err := json.Unmarshal(data, &p); err != nil {
		return nil, fmt.Errorf("invalid preset %q: %w", name, err)
	}
	return &p, nil
}

// LoadAllPresets loads every preset in AllPresetNames.
func LoadAllPresets() ([]*Preset, error) {
	var presets []*Preset
	for _, name := range AllPresetNames {
		p, err := LoadPreset(name)
		if err != nil {
			continue // skip broken presets
		}
		presets = append(presets, p)
	}
	if len(presets) == 0 {
		return nil, fmt.Errorf("no presets could be loaded")
	}
	return presets, nil
}

// PresetsForMood returns up to 3 preset names matching the given mood.
func PresetsForMood(mood string) []string {
	mood = strings.ToLower(strings.TrimSpace(mood))
	if names, ok := MoodMap[mood]; ok {
		return names
	}
	// Substring match fallback
	for key, names := range MoodMap {
		if strings.Contains(mood, key) || strings.Contains(key, mood) {
			return names
		}
	}
	// Default: one from each category
	return []string{"bold_signal", "notebook_tabs", "neon_cyber"}
}

// PresetSummary is a condensed view of a preset for display.
type PresetSummary struct {
	Name        string `json:"name"`
	DisplayName string `json:"display_name"`
	Category    string `json:"category"`
	Vibe        string `json:"vibe"`
	Description string `json:"description"`
}

// ListPresets returns a summary of every available preset.
func ListPresets() ([]PresetSummary, error) {
	presets, err := LoadAllPresets()
	if err != nil {
		return nil, err
	}
	var out []PresetSummary
	for _, p := range presets {
		out = append(out, PresetSummary{
			Name:        p.Name,
			DisplayName: p.DisplayName,
			Category:    p.Category,
			Vibe:        p.Vibe,
			Description: p.Description,
		})
	}
	return out, nil
}
