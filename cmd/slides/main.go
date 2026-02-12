// Slide Builder CLI — root command.
//
// A CLI tool for creating stunning HTML presentations, powered by
// GitHub Copilot and curated style presets.
package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var version = "2.0.0"

var rootCmd = &cobra.Command{
	Use:   "slides",
	Short: "Create stunning HTML presentations",
	Long: `Slide Builder — Create stunning, animation-rich HTML presentations
from scratch or by converting PowerPoint files.

Powered by GitHub Copilot, AI agent team, and 10 curated style presets.
Works as a standalone CLI or via MCP server for VS Code Copilot integration.

Examples:
  slides new --topic "AI Startup Pitch" --style neon_cyber --output pitch.html
  slides research --topic "Climate Change" --urls "https://..." --formats html,pptx,pdf
  slides edit --instruction "Change slide 3 to a quote"
  slides convert presentation.pptx --style bold_signal --output web-slides.html
  slides preview --mood excited --output ./previews/
  slides list-styles`,
	Version: version,
}

func init() {
	rootCmd.AddCommand(newCmd)
	rootCmd.AddCommand(convertCmd)
	rootCmd.AddCommand(previewCmd)
	rootCmd.AddCommand(listStylesCmd)
	rootCmd.AddCommand(researchCmd)
	rootCmd.AddCommand(editCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
