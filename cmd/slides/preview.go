package main

import (
	"fmt"
	"path/filepath"

	"github.com/spf13/cobra"

	"github.com/sameerankalgi/slide-builder-ghcp/internal/generator"
	"github.com/sameerankalgi/slide-builder-ghcp/internal/styles"
)

var (
	previewMood     string
	previewOutput   string
	previewTitle    string
	previewSubtitle string
)

var previewCmd = &cobra.Command{
	Use:   "preview",
	Short: "Generate style preview HTML files by mood",
	Long: `Generate 3 style preview files based on a mood keyword.
This is the "show, don't tell" approach — instead of describing styles
in words, see actual visual previews in your browser.

Moods: impressed, confident, excited, energized, calm, focused,
       inspired, moved, professional, playful, technical, elegant`,
	Example: `  slides preview --mood excited --output ./previews/
  slides preview --mood professional --title "Q4 Results"`,
	RunE: runPreview,
}

func init() {
	previewCmd.Flags().StringVar(&previewMood, "mood", "impressed", "Desired audience feeling")
	previewCmd.Flags().StringVar(&previewOutput, "output", "./slide-previews", "Output directory")
	previewCmd.Flags().StringVar(&previewTitle, "title", "Your Presentation Title", "Title for previews")
	previewCmd.Flags().StringVar(&previewSubtitle, "subtitle", "A beautiful slide deck crafted just for you", "Subtitle for previews")
}

func runPreview(cmd *cobra.Command, args []string) error {
	presetNames := styles.PresetsForMood(previewMood)
	fmt.Printf("\n  Generating 3 style previews for mood: %s\n\n", previewMood)

	for i, name := range presetNames {
		if i >= 3 {
			break
		}

		p, err := styles.LoadPreset(name)
		if err != nil {
			fmt.Printf("  Warning: Skipping %s: %v\n", name, err)
			continue
		}

		suffix := string(rune('a' + i))
		outPath := filepath.Join(previewOutput, fmt.Sprintf("style-%s.html", suffix))

		if err := generator.GeneratePreview(name, outPath, previewTitle, previewSubtitle); err != nil {
			fmt.Printf("  Warning: Error generating %s: %v\n", name, err)
			continue
		}

		label := string(rune('A' + i))
		fmt.Printf("  Style %s: %s — %s\n", label, p.DisplayName, p.Vibe)
		fmt.Printf("    %s\n\n", outPath)
	}

	fmt.Println("Open each file in your browser to compare them.")
	fmt.Printf("Then use: slides new --style <name> --output presentation.html\n\n")

	return nil
}
