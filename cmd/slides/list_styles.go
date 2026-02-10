package main

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"github.com/sameerankalgi/slide-builder-ghcp/internal/styles"
)

var listStylesCmd = &cobra.Command{
	Use:   "list-styles",
	Short: "List all available style presets",
	Long:  "Display all 10 curated style presets with their category, vibe, and description.",
	RunE:  runListStyles,
}

func runListStyles(cmd *cobra.Command, args []string) error {
	summaries, err := styles.ListPresets()
	if err != nil {
		return fmt.Errorf("loading presets: %w", err)
	}

	fmt.Println("\n  Available Style Presets")
	fmt.Println(strings.Repeat("─", 60))

	currentCategory := ""
	for _, s := range summaries {
		if s.Category != currentCategory {
			currentCategory = s.Category
			fmt.Printf("\n  %s Themes\n", capitalize(currentCategory))
			fmt.Println(strings.Repeat("─", 40))
		}
		fmt.Printf("  %-20s %s\n", s.DisplayName, s.Name)
		fmt.Printf("  %-20s %s\n", "", s.Vibe)
		fmt.Printf("  %-20s %s\n\n", "", s.Description)
	}

	fmt.Println("Use a preset with: slides new --style <name>")
	fmt.Println("Preview styles:    slides preview --mood <mood>")

	return nil
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}
