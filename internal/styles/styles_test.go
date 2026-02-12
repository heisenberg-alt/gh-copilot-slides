package styles

import (
	"testing"
)

func TestLoadPreset(t *testing.T) {
	t.Run("loads existing preset", func(t *testing.T) {
		p, err := LoadPreset("bold_signal")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if p.Name != "bold_signal" {
			t.Errorf("expected name 'bold_signal', got %q", p.Name)
		}
		if p.DisplayName == "" {
			t.Error("expected non-empty display name")
		}
		if len(p.Colors) == 0 {
			t.Error("expected colors to be populated")
		}
		if len(p.Fonts) == 0 {
			t.Error("expected fonts to be populated")
		}
	})

	t.Run("all known presets load", func(t *testing.T) {
		for _, name := range AllPresetNames {
			p, err := LoadPreset(name)
			if err != nil {
				t.Errorf("failed to load preset %q: %v", name, err)
				continue
			}
			if p.DisplayName == "" {
				t.Errorf("preset %q has empty display_name", name)
			}
		}
	})

	t.Run("nonexistent preset returns error", func(t *testing.T) {
		_, err := LoadPreset("does_not_exist_xyz")
		if err == nil {
			t.Error("expected error for nonexistent preset")
		}
	})
}

func TestLoadAllPresets(t *testing.T) {
	presets, err := LoadAllPresets()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(presets) != len(AllPresetNames) {
		t.Errorf("expected %d presets, got %d", len(AllPresetNames), len(presets))
	}
	for _, p := range presets {
		if p.DisplayName == "" {
			t.Errorf("preset %q has empty display name", p.Name)
		}
	}
}

func TestPresetsForMood(t *testing.T) {
	tests := []struct {
		mood    string
		wantLen int
		exact   []string
	}{
		{"excited", 3, MoodMap["excited"]},
		{"EXCITED", 3, MoodMap["excited"]},
		{"professional", 3, MoodMap["professional"]},
		{"nonsensical_mood_xyz", 3, nil},
	}

	for _, tc := range tests {
		t.Run(tc.mood, func(t *testing.T) {
			result := PresetsForMood(tc.mood)
			if len(result) != tc.wantLen {
				t.Errorf("PresetsForMood(%q): got %d results, want %d",
					tc.mood, len(result), tc.wantLen)
			}
			if tc.exact != nil {
				for i, name := range tc.exact {
					if i < len(result) && result[i] != name {
						t.Errorf("PresetsForMood(%q)[%d] = %q, want %q",
							tc.mood, i, result[i], name)
					}
				}
			}
		})
	}
}

func TestListPresets(t *testing.T) {
	summaries, err := ListPresets()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(summaries) != len(AllPresetNames) {
		t.Errorf("expected %d summaries, got %d", len(AllPresetNames), len(summaries))
	}
	for _, s := range summaries {
		if s.DisplayName == "" {
			t.Errorf("summary for %q has empty display_name", s.Name)
		}
		if s.Category == "" {
			t.Errorf("summary for %q has empty category", s.Name)
		}
	}
}

func TestMoodMapCoverage(t *testing.T) {
	valid := make(map[string]bool)
	for _, n := range AllPresetNames {
		valid[n] = true
	}
	for mood, presets := range MoodMap {
		if len(presets) > 3 {
			t.Errorf("mood %q has %d presets, max is 3", mood, len(presets))
		}
		for _, p := range presets {
			if !valid[p] {
				t.Errorf("mood %q references unknown preset %q", mood, p)
			}
		}
	}
}
