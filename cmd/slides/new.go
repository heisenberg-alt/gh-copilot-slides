package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/charmbracelet/huh"
	"github.com/spf13/cobra"

	"github.com/sameerankalgi/slide-builder-ghcp/internal/copilot"
	"github.com/sameerankalgi/slide-builder-ghcp/internal/generator"
	"github.com/sameerankalgi/slide-builder-ghcp/internal/styles"
)

var (
	newTopic       string
	newPurpose     string
	newStyle       string
	newOutput      string
	newSlideCount  int
	newInteractive bool
)

var newCmd = &cobra.Command{
	Use:   "new",
	Short: "Create a new presentation from scratch",
	Long: `Create a new HTML presentation interactively or from flags.

In interactive mode (default), you will be guided through:
1. Content discovery - topic, purpose, slide count
2. Style discovery - mood-based preset selection with previews
3. Generation - full HTML presentation output

In non-interactive mode, provide --topic, --style, and --output.`,
	Example: `  slides new
  slides new --topic "AI Startup Pitch" --purpose pitch --style neon_cyber --output pitch.html
  echo '[{"type":"title","title":"Hello"}]' | slides new --style bold_signal --output hello.html`,
	RunE: runNew,
}

func init() {
	newCmd.Flags().StringVar(&newTopic, "topic", "", "Presentation topic")
	newCmd.Flags().StringVar(&newPurpose, "purpose", "presentation", "Purpose: pitch, teaching, conference, internal")
	newCmd.Flags().StringVar(&newStyle, "style", "", "Style preset name")
	newCmd.Flags().StringVar(&newOutput, "output", "", "Output file path")
	newCmd.Flags().IntVar(&newSlideCount, "slides", 10, "Number of slides to generate")
	newCmd.Flags().BoolVar(&newInteractive, "interactive", true, "Run in interactive mode")
}

func runNew(cmd *cobra.Command, args []string) error {
	// Validate slide count range
	if newSlideCount < 1 || newSlideCount > 100 {
		return fmt.Errorf("slide count must be between 1 and 100, got %d", newSlideCount)
	}
	if newTopic != "" && newStyle != "" && newOutput != "" {
		return runNewNonInteractive()
	}
	if !newInteractive {
		return fmt.Errorf("non-interactive mode requires --topic, --style, and --output flags")
	}
	return runNewInteractive()
}

func runNewInteractive() error {
	fmt.Println("\n  Slide Builder - Create a New Presentation")

	var topic, purpose, mood, styleName string
	var slideCount int

	form := huh.NewForm(
		huh.NewGroup(
			huh.NewInput().
				Title("What is this presentation about?").
				Placeholder("e.g., AI Startup Pitch Deck").
				Value(&topic),
			huh.NewSelect[string]().
				Title("What is the purpose?").
				Options(
					huh.NewOption("Pitch deck - Selling an idea, product, or company", "pitch"),
					huh.NewOption("Teaching/Tutorial - Explaining concepts", "teaching"),
					huh.NewOption("Conference talk - Speaking at an event", "conference"),
					huh.NewOption("Internal presentation - Team updates, strategy", "internal"),
				).
				Value(&purpose),
			huh.NewSelect[int]().
				Title("How many slides?").
				Options(
					huh.NewOption("Short (5-8)", 6),
					huh.NewOption("Medium (10-15)", 12),
					huh.NewOption("Long (20+)", 20),
				).
				Value(&slideCount),
		),
	)

	if err := form.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}

	moodForm := huh.NewForm(
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("How do you want your audience to feel?").
				Options(
					huh.NewOption("Impressed & Confident", "impressed"),
					huh.NewOption("Excited & Energized", "excited"),
					huh.NewOption("Calm & Focused", "calm"),
					huh.NewOption("Inspired & Moved", "inspired"),
					huh.NewOption("Professional & Trustworthy", "professional"),
					huh.NewOption("Playful & Creative", "playful"),
					huh.NewOption("Technical & Precise", "technical"),
					huh.NewOption("Elegant & Sophisticated", "elegant"),
				).
				Value(&mood),
		),
	)

	if err := moodForm.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}

	presetNames := styles.PresetsForMood(mood)
	fmt.Printf("\n  Based on mood (%s), matching styles:\n\n", mood)

	styleOptions := make([]huh.Option[string], 0, len(presetNames))
	for _, name := range presetNames {
		p, err := styles.LoadPreset(name)
		if err != nil {
			continue
		}
		label := fmt.Sprintf("%s - %s", p.DisplayName, p.Vibe)
		styleOptions = append(styleOptions, huh.NewOption(label, name))
	}

	styleForm := huh.NewForm(
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("Pick a style").
				Options(styleOptions...).
				Value(&styleName),
		),
	)

	if err := styleForm.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}

	var outputPath string
	outForm := huh.NewForm(
		huh.NewGroup(
			huh.NewInput().
				Title("Output file path").
				Placeholder("presentation.html").
				Value(&outputPath),
		),
	)

	if err := outForm.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}
	if outputPath == "" {
		outputPath = "presentation.html"
	}

	fmt.Println("\n  Generating slide content with GitHub Copilot...")

	client := copilot.NewClient("")
	slidesJSON, err := client.GenerateSlideContent(topic, purpose, slideCount, "")
	if err != nil {
		fmt.Printf("  Copilot unavailable (%v), generating sample slides...\n", err)
		return generateSamplePresentation(topic, styleName, outputPath)
	}

	slidesJSON = cleanJSON(slidesJSON)

	var slides []generator.Slide
	if err := json.Unmarshal([]byte(slidesJSON), &slides); err != nil {
		fmt.Printf("  Could not parse Copilot response, generating sample slides...\n")
		return generateSamplePresentation(topic, styleName, outputPath)
	}

	if err := generator.GeneratePresentation(topic, slides, styleName, outputPath); err != nil {
		return fmt.Errorf("generating presentation: %w", err)
	}

	printSuccess(outputPath, styleName, len(slides))
	return nil
}

func runNewNonInteractive() error {
	stat, _ := os.Stdin.Stat()
	if (stat.Mode() & os.ModeCharDevice) == 0 {
		var slides []generator.Slide
		if err := json.NewDecoder(os.Stdin).Decode(&slides); err != nil {
			return fmt.Errorf("parsing slides JSON from stdin: %w", err)
		}
		if err := generator.GeneratePresentation(newTopic, slides, newStyle, newOutput); err != nil {
			return fmt.Errorf("generating presentation: %w", err)
		}
		fmt.Printf("Generated %s (%d slides, style: %s)\n", newOutput, len(slides), newStyle)
		return nil
	}

	client := copilot.NewClient("")
	slidesJSON, err := client.GenerateSlideContent(newTopic, newPurpose, newSlideCount, "")
	if err != nil {
		fmt.Printf("Copilot unavailable, generating sample slides...\n")
		return generateSamplePresentation(newTopic, newStyle, newOutput)
	}

	slidesJSON = cleanJSON(slidesJSON)

	var slides []generator.Slide
	if err := json.Unmarshal([]byte(slidesJSON), &slides); err != nil {
		return generateSamplePresentation(newTopic, newStyle, newOutput)
	}

	if err := generator.GeneratePresentation(newTopic, slides, newStyle, newOutput); err != nil {
		return fmt.Errorf("generating presentation: %w", err)
	}

	fmt.Printf("Generated %s (%d slides, style: %s)\n", newOutput, len(slides), newStyle)
	return nil
}

func cleanJSON(s string) string {
	s = strings.TrimSpace(s)
	s = strings.TrimPrefix(s, "```json")
	s = strings.TrimPrefix(s, "```")
	s = strings.TrimSuffix(s, "```")
	return strings.TrimSpace(s)
}

func generateSamplePresentation(topic, styleName, outputPath string) error {
	slides := []generator.Slide{
		{
			Type:     "title",
			Title:    topic,
			Subtitle: "A presentation built with Slide Builder",
		},
		{
			Type:  "content",
			Title: "Overview",
			Bullets: []string{
				"Key point one - describe your main idea",
				"Key point two - supporting evidence",
				"Key point three - implications and impact",
				"Key point four - next steps",
			},
		},
		{
			Type:  "feature_grid",
			Title: "Key Features",
			Cards: []generator.Card{
				{Title: "Feature 1", Description: "Description of the first key feature", Icon: "R"},
				{Title: "Feature 2", Description: "Description of the second key feature", Icon: "Z"},
				{Title: "Feature 3", Description: "Description of the third key feature", Icon: "T"},
				{Title: "Feature 4", Description: "Description of the fourth key feature", Icon: "L"},
			},
		},
		{
			Type:        "quote",
			Quote:       "The best way to predict the future is to create it.",
			Attribution: "Peter Drucker",
		},
		{
			Type:     "closing",
			Title:    "Thank You",
			Subtitle: "Questions & Discussion",
		},
	}

	if err := generator.GeneratePresentation(topic, slides, styleName, outputPath); err != nil {
		return fmt.Errorf("generating presentation: %w", err)
	}

	printSuccess(outputPath, styleName, len(slides))
	return nil
}

func printSuccess(outputPath, styleName string, slideCount int) {
	fmt.Printf("\n  Presentation created!\n")
	fmt.Printf("  File:   %s\n", outputPath)
	fmt.Printf("  Style:  %s\n", styleName)
	fmt.Printf("  Slides: %d\n", slideCount)
	fmt.Printf("\n  Open in browser: open %s\n\n", outputPath)
}
