package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"

	"github.com/charmbracelet/huh"
	"github.com/spf13/cobra"

	"github.com/sameerankalgi/slide-builder-ghcp/internal/styles"
)

var (
	convertStyle  string
	convertOutput string
)

var convertCmd = &cobra.Command{
	Use:   "convert [file.pptx]",
	Short: "Convert a PowerPoint file to an HTML presentation",
	Long: `Convert an existing .pptx file to a beautiful web presentation.

Uses Python (python-pptx) under the hood to extract content and images,
then generates HTML with the chosen style preset.

Requires: Python 3.10+ with python-pptx installed.
Install: pip install python-pptx`,
	Example: `  slides convert deck.pptx --style bold_signal --output web-deck.html
  slides convert deck.pptx  # interactive style selection`,
	Args: cobra.ExactArgs(1),
	RunE: runConvert,
}

func init() {
	convertCmd.Flags().StringVar(&convertStyle, "style", "", "Style preset name")
	convertCmd.Flags().StringVar(&convertOutput, "output", "", "Output HTML file path")
}

func runConvert(cmd *cobra.Command, args []string) error {
	pptxPath := args[0]

	// Determine output path
	if convertOutput == "" {
		base := filepath.Base(pptxPath)
		ext := filepath.Ext(base)
		convertOutput = base[:len(base)-len(ext)] + ".html"
	}

	// Interactive style selection if not provided
	if convertStyle == "" {
		var mood string
		moodForm := huh.NewForm(
			huh.NewGroup(
				huh.NewSelect[string]().
					Title("How do you want the converted presentation to feel?").
					Options(
						huh.NewOption("Impressed & Confident", "impressed"),
						huh.NewOption("Excited & Energized", "excited"),
						huh.NewOption("Calm & Focused", "calm"),
						huh.NewOption("Inspired & Moved", "inspired"),
						huh.NewOption("Professional & Trustworthy", "professional"),
						huh.NewOption("Technical & Precise", "technical"),
					).
					Value(&mood),
			),
		)

		if err := moodForm.Run(); err != nil {
			return fmt.Errorf("form cancelled: %w", err)
		}

		presetNames := styles.PresetsForMood(mood)
		options := make([]huh.Option[string], 0)
		for _, name := range presetNames {
			p, err := styles.LoadPreset(name)
			if err != nil {
				continue
			}
			options = append(options, huh.NewOption(
				fmt.Sprintf("%s — %s", p.DisplayName, p.Vibe), name,
			))
		}

		styleForm := huh.NewForm(
			huh.NewGroup(
				huh.NewSelect[string]().
					Title("Pick a style").
					Options(options...).
					Value(&convertStyle),
			),
		)

		if err := styleForm.Run(); err != nil {
			return fmt.Errorf("form cancelled: %w", err)
		}
	}

	// Validate style exists
	if _, err := styles.LoadPreset(convertStyle); err != nil {
		return fmt.Errorf("invalid style: %w", err)
	}

	fmt.Printf("\nConverting %s with style: %s ...\n", pptxPath, convertStyle)

	// Call Python converter via subprocess — params passed via temp JSON file
	outputDir := filepath.Dir(convertOutput)
	if outputDir == "" || outputDir == "." {
		outputDir = "."
	}

	params := map[string]any{
		"pptx_path":   pptxPath,
		"output_dir":  outputDir,
		"style_name":  convertStyle,
		"output_path": convertOutput,
	}
	paramsFile, err := writeTempJSON(params)
	if err != nil {
		return fmt.Errorf("writing params: %w", err)
	}
	defer os.Remove(paramsFile)

	pyScript := `
import sys, os, json

params = json.load(open(sys.argv[1]))
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))
from slide_mcp.ppt_converter import pptx_to_slides
from slide_mcp.generator import generate_presentation

slides = pptx_to_slides(params["pptx_path"], params["output_dir"])
title = slides[0]['title'] if slides and slides[0].get('title') else 'Presentation'
result = generate_presentation(title, slides, params["style_name"], params["output_path"])
print("Generated: " + result)
print("Slides: " + str(len(slides)))
`

	pyCmd := exec.Command("python3", "-c", pyScript, paramsFile)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	if err := pyCmd.Run(); err != nil {
		return fmt.Errorf("Python conversion failed: %w\nMake sure Python 3.10+ with python-pptx is installed:\n  pip install python-pptx jinja2", err)
	}

	fmt.Printf("\nConversion complete!\n")
	fmt.Printf("  HTML:   %s\n", convertOutput)
	fmt.Printf("  Style:  %s\n", convertStyle)
	fmt.Printf("  Assets: %s/assets/\n", outputDir)

	if runtime.GOOS == "darwin" {
		fmt.Printf("\n  Open: open %s\n\n", convertOutput)
	}

	return nil
}
