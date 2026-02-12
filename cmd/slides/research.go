package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"

	"github.com/charmbracelet/huh"
	"github.com/spf13/cobra"
)

var (
	researchTopic        string
	researchURLs         string
	researchFiles        string
	researchStyle        string
	researchMood         string
	researchOutput       string
	researchFormats      string
	researchSlideCount   int
	researchPurpose      string
	researchAudience     string
	researchEdit         bool
	researchPPTXTemplate string
)

var researchCmd = &cobra.Command{
	Use:   "research",
	Short: "Create a research-driven presentation using the AI agent pipeline",
	Long: `Create a presentation by researching a topic using AI agents.

The pipeline:
  1. Research Agent — gathers content from URLs, web search, and local files
  2. Curator Agent — structures research into slides with narrative arc
  3. Style Recommender — picks the best visual theme
  4. Exporters — generates output in HTML, PPTX, and/or PDF

After generation, optionally enter an edit loop to refine the presentation.

Requires: Python 3.10+ with slide_mcp dependencies installed.`,
	Example: `  slides research --topic "AI in Healthcare" --formats html,pptx,pdf
  slides research --topic "Q4 Results" --urls "https://example.com/report" --style bold_signal
  slides research --topic "Climate Change" --files data.pdf,notes.md --edit
  slides research  # interactive mode`,
	RunE: runResearch,
}

func init() {
	researchCmd.Flags().StringVar(&researchTopic, "topic", "", "Presentation topic")
	researchCmd.Flags().StringVar(&researchURLs, "urls", "", "Comma-separated URLs to research from")
	researchCmd.Flags().StringVar(&researchFiles, "files", "", "Comma-separated local file paths")
	researchCmd.Flags().StringVar(&researchStyle, "style", "", "Style preset name (empty for AI recommendation)")
	researchCmd.Flags().StringVar(&researchMood, "mood", "", "Desired mood: impressed, excited, calm, professional, etc.")
	researchCmd.Flags().StringVar(&researchOutput, "output", ".", "Output directory")
	researchCmd.Flags().StringVar(&researchFormats, "formats", "html", "Comma-separated output formats: html,pptx,pdf")
	researchCmd.Flags().IntVar(&researchSlideCount, "slides", 10, "Number of slides to create")
	researchCmd.Flags().StringVar(&researchPurpose, "purpose", "presentation", "Purpose: pitch, teaching, conference, internal")
	researchCmd.Flags().StringVar(&researchAudience, "audience", "", "Target audience description")
	researchCmd.Flags().BoolVar(&researchEdit, "edit", false, "Enter edit loop after generation")
	researchCmd.Flags().StringVar(&researchPPTXTemplate, "pptx-template", "", "PPTX template file for theming")
}

func runResearch(cmd *cobra.Command, args []string) error {
	// Validate slide count range
	if researchSlideCount < 1 || researchSlideCount > 100 {
		return fmt.Errorf("slide count must be between 1 and 100, got %d", researchSlideCount)
	}
	// Interactive mode if no topic provided
	if researchTopic == "" {
		return runResearchInteractive(cmd)
	}
	return runResearchDirect(cmd)
}

func runResearchInteractive(cmd *cobra.Command) error {
	fmt.Println("\n  Slide Builder — Research-Driven Presentation")
	fmt.Println("  Powered by AI Agent Team")

	var topic, purpose, mood, audience, urls, files, outputDir, formats string
	var slideCount int

	form := huh.NewForm(
		huh.NewGroup(
			huh.NewInput().
				Title("What topic should the presentation cover?").
				Placeholder("e.g., The Future of Renewable Energy").
				Value(&topic),
			huh.NewInput().
				Title("Any URLs to research from? (comma-separated, or leave empty)").
				Placeholder("https://example.com/article1, https://example.com/article2").
				Value(&urls),
			huh.NewInput().
				Title("Any local files to include? (comma-separated, or leave empty)").
				Placeholder("report.pdf, notes.md, data.csv").
				Value(&files),
		),
	)

	if err := form.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}

	detailsForm := huh.NewForm(
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("What is the purpose?").
				Options(
					huh.NewOption("Pitch deck", "pitch"),
					huh.NewOption("Teaching/Tutorial", "teaching"),
					huh.NewOption("Conference talk", "conference"),
					huh.NewOption("Internal presentation", "internal"),
					huh.NewOption("General presentation", "presentation"),
				).
				Value(&purpose),
			huh.NewInput().
				Title("Who is the target audience?").
				Placeholder("e.g., Tech executives, College students").
				Value(&audience),
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

	if err := detailsForm.Run(); err != nil {
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
					huh.NewOption("Let AI decide", ""),
				).
				Value(&mood),
		),
	)

	if err := moodForm.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}

	formatsForm := huh.NewForm(
		huh.NewGroup(
			huh.NewInput().
				Title("Output formats (comma-separated: html, pptx, pdf)").
				Placeholder("html,pptx").
				Value(&formats),
			huh.NewInput().
				Title("Output directory").
				Placeholder("./output").
				Value(&outputDir),
		),
	)

	if err := formatsForm.Run(); err != nil {
		return fmt.Errorf("form cancelled: %w", err)
	}

	if formats == "" {
		formats = "html"
	}
	if outputDir == "" {
		outputDir = "."
	}

	researchTopic = topic
	researchURLs = urls
	researchFiles = files
	researchPurpose = purpose
	researchAudience = audience
	researchSlideCount = slideCount
	researchMood = mood
	researchFormats = formats
	researchOutput = outputDir

	return runResearchDirect(cmd)
}

func runResearchDirect(cmd *cobra.Command) error {
	// Parse comma-separated values
	urlList := parseCSV(researchURLs)
	fileList := parseCSV(researchFiles)
	formatList := parseCSV(researchFormats)

	if len(formatList) == 0 {
		formatList = []string{"html"}
	}

	fmt.Printf("\n  Researching: %s\n", researchTopic)
	if len(urlList) > 0 {
		fmt.Printf("  URLs: %d source(s)\n", len(urlList))
	}
	if len(fileList) > 0 {
		fmt.Printf("  Files: %d file(s)\n", len(fileList))
	}
	fmt.Printf("  Formats: %s\n", strings.Join(formatList, ", "))
	fmt.Printf("  Running AI agent pipeline...\n\n")

	// Build params as JSON and write to a temp file (avoids shell injection)
	params := map[string]any{
		"topic":          researchTopic,
		"urls":           urlList,
		"files":          fileList,
		"slide_count":    researchSlideCount,
		"purpose":        researchPurpose,
		"mood":           researchMood,
		"audience":       researchAudience,
		"style_name":     researchStyle,
		"pptx_template":  researchPPTXTemplate,
		"output_dir":     researchOutput,
		"output_formats": formatList,
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
from slide_mcp.agents.orchestrator import Orchestrator

pptx_template = params.get("pptx_template") or None

orch = Orchestrator()
session = orch.create_presentation(
    topic=params["topic"],
    urls=params.get("urls", []),
    files=params.get("files", []),
    slide_count=params.get("slide_count", 10),
    purpose=params.get("purpose", "presentation"),
    mood=params.get("mood", ""),
    audience=params.get("audience", ""),
    style_name=params.get("style_name", ""),
    pptx_template=pptx_template,
    output_dir=params.get("output_dir", "."),
    output_formats=params.get("output_formats", ["html"]),
)

print("SESSION_ID:" + session.id)
print("TITLE:" + session.presentation_title)
print("STYLE:" + session.style_name)
print("SLIDES:" + str(len(session.slides)))
for fmt, path in session.output_paths.items():
    print(f"OUTPUT:{fmt}:{path}")
for i, s in enumerate(session.slides):
    print(f"SLIDE:{i+1}:[{s.get('type','content')}] {s.get('title','Untitled')}")
`

	pyCmd := exec.Command("python3", "-c", pyScript, paramsFile)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	if err := pyCmd.Run(); err != nil {
		return fmt.Errorf(
			"Pipeline failed: %w\nMake sure Python 3.10+ with all dependencies is installed:\n"+
				"  pip install -e '.[research]'",
			err,
		)
	}

	fmt.Println("\n  Pipeline complete!")

	if researchEdit {
		fmt.Println("\n  Entering edit mode... (type 'done' to finish)")
		return runEditLoop(cmd)
	}

	if runtime.GOOS == "darwin" {
		fmt.Println("\n  Tip: open the HTML file with: open <filename>.html")
	}

	return nil
}

func runEditLoop(cmd *cobra.Command) error {
	for {
		var instruction string
		form := huh.NewForm(
			huh.NewGroup(
				huh.NewInput().
					Title("Edit instruction (or 'done' to finish)").
					Placeholder("e.g., Change slide 3 to a quote slide").
					Value(&instruction),
			),
		)

		if err := form.Run(); err != nil {
			return nil // User cancelled
		}

		instruction = strings.TrimSpace(instruction)
		if instruction == "" || instruction == "done" || instruction == "quit" || instruction == "exit" {
			fmt.Println("\n  Edit session complete.")
			return nil
		}

		fmt.Printf("\n  Applying edit: %s\n", instruction)

		// Write edit params to a temp JSON file
		editParams := map[string]any{
			"instruction": instruction,
		}
		editFile, err := writeTempJSON(editParams)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}

		pyScript := `
import sys, os, json

params = json.load(open(sys.argv[1]))
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))
from slide_mcp.agents.orchestrator import Orchestrator

orch = Orchestrator()
sessions = orch.list_sessions()
if not sessions:
    print("ERROR: No sessions found")
    sys.exit(1)

session_id = sessions[0]['id']
session = orch.edit_presentation(session_id, params["instruction"])
print("UPDATED: " + str(len(session.slides)) + " slides")
if session.edit_history:
    latest = session.edit_history[-1]
    print("CHANGES: " + latest.get('summary', 'Updated'))
for fmt, path in session.output_paths.items():
    print(f"OUTPUT:{fmt}:{path}")
`

		pyCmd := exec.Command("python3", "-c", pyScript, editFile)
		pyCmd.Stdout = cmd.OutOrStdout()
		pyCmd.Stderr = cmd.ErrOrStderr()

		if err := pyCmd.Run(); err != nil {
			fmt.Printf("  Edit failed: %v\n", err)
		}
		os.Remove(editFile)
	}
}

func parseCSV(s string) []string {
	if s == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	result := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			result = append(result, p)
		}
	}
	return result
}

// writeTempJSON marshals data to a temporary JSON file and returns its path.
// The caller is responsible for removing the file when done.
func writeTempJSON(data any) (string, error) {
	f, err := os.CreateTemp("", "slide-builder-*.json")
	if err != nil {
		return "", fmt.Errorf("creating temp file: %w", err)
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(data); err != nil {
		os.Remove(f.Name())
		return "", fmt.Errorf("encoding JSON: %w", err)
	}
	return f.Name(), nil
}
