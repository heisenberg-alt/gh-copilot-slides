package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/charmbracelet/huh"
	"github.com/spf13/cobra"
)

var (
	editSession     string
	editInstruction string
	editStyle       string
	editExport      string
)

var editCmd = &cobra.Command{
	Use:   "edit",
	Short: "Edit an existing presentation session",
	Long: `Edit a previously generated presentation using natural language instructions.

You can modify content, reorder slides, change types, add/remove slides,
refine wording, change the style, or re-export to different formats.

Without --instruction, enters an interactive edit loop.

Requires: Python 3.10+ with slide_mcp dependencies installed.`,
	Example: `  slides edit --instruction "Change slide 3 to a quote slide"
  slides edit --session abc123 --instruction "Add more data to slide 5"
  slides edit --style neon_cyber
  slides edit --export pptx,pdf
  slides edit  # interactive loop on latest session`,
	RunE: runEdit,
}

func init() {
	editCmd.Flags().StringVar(&editSession, "session", "", "Session ID (default: latest session)")
	editCmd.Flags().StringVar(&editInstruction, "instruction", "", "Edit instruction (natural language)")
	editCmd.Flags().StringVar(&editStyle, "style", "", "Change style to this preset")
	editCmd.Flags().StringVar(&editExport, "export", "", "Re-export to these formats (comma-separated: html,pptx,pdf)")
}

func runEdit(cmd *cobra.Command, args []string) error {
	// If style change requested
	if editStyle != "" {
		return changeStyle(cmd)
	}
	// If export requested
	if editExport != "" {
		return reExport(cmd)
	}
	// If instruction provided directly
	if editInstruction != "" {
		return editDirect(cmd)
	}
	// Interactive edit loop
	return editInteractive(cmd)
}

func editDirect(cmd *cobra.Command) error {
	sessionSelector := getSessionSelector()

	params := map[string]any{
		"session_selector": sessionSelector,
		"instruction":      editInstruction,
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

orch = Orchestrator()
session_selector = params.get("session_selector", "")
if session_selector:
    session_id = session_selector
else:
    sessions = orch.list_sessions()
    if not sessions:
        print("No sessions found.")
        sys.exit(1)
    session_id = sessions[0]['id']

session = orch.edit_presentation(session_id, params["instruction"])
print("Session: " + session.id)
print("Slides: " + str(len(session.slides)))
if session.edit_history:
    print("Changes: " + session.edit_history[-1].get('summary', 'Updated'))
for fmt, path in session.output_paths.items():
    if not path.startswith("ERROR"):
        print(f"  {fmt.upper()}: {path}")
`

	pyCmd := exec.Command("python3", "-c", pyScript, paramsFile)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	if err := pyCmd.Run(); err != nil {
		return fmt.Errorf("edit failed: %w", err)
	}
	return nil
}

func editInteractive(cmd *cobra.Command) error {
	fmt.Println("\n  Slide Builder — Edit Mode")
	fmt.Println("  Commands: type edit instruction, 'style <name>', 'export <formats>', or 'done'")

	// Show current session info
	listParams := map[string]any{"action": "list"}
	listFile, err := writeTempJSON(listParams)
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		listPyScript := `
import sys, os, json

json.load(open(sys.argv[1]))  # validate
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))
from slide_mcp.agents.orchestrator import Orchestrator

orch = Orchestrator()
sessions = orch.list_sessions()
if not sessions:
    print("No sessions found. Create one with: slides research --topic 'Your Topic'")
else:
    s = sessions[0]
    print(f"Session: {s['id']} — {s.get('topic', 'Untitled')} ({s.get('slides', '0')} slides)")
`
		listCmd := exec.Command("python3", "-c", listPyScript, listFile)
		listCmd.Stdout = cmd.OutOrStdout()
		listCmd.Stderr = cmd.ErrOrStderr()
		listCmd.Run()
		os.Remove(listFile)
	}

	// Edit loop
	for {
		var instruction string
		form := huh.NewForm(
			huh.NewGroup(
				huh.NewInput().
					Title("Edit instruction").
					Placeholder("e.g., Make slide 2 bullets more concise (or 'done')").
					Value(&instruction),
			),
		)

		if err := form.Run(); err != nil {
			return nil
		}

		instruction = strings.TrimSpace(instruction)
		if instruction == "" || instruction == "done" || instruction == "quit" || instruction == "exit" {
			fmt.Println("\n  Edit session complete.")
			return nil
		}

		// Handle special commands
		if strings.HasPrefix(instruction, "style ") {
			editStyle = strings.TrimPrefix(instruction, "style ")
			if err := changeStyle(cmd); err != nil {
				fmt.Printf("  Error: %v\n", err)
			}
			continue
		}

		if strings.HasPrefix(instruction, "export ") {
			editExport = strings.TrimPrefix(instruction, "export ")
			if err := reExport(cmd); err != nil {
				fmt.Printf("  Error: %v\n", err)
			}
			continue
		}

		// Regular edit instruction
		editInstruction = instruction
		if err := editDirect(cmd); err != nil {
			fmt.Printf("  Error: %v\n", err)
		}
	}
}

func changeStyle(cmd *cobra.Command) error {
	sessionSelector := getSessionSelector()

	params := map[string]any{
		"session_selector": sessionSelector,
		"style_name":       editStyle,
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

orch = Orchestrator()
session_selector = params.get("session_selector", "")
if session_selector:
    session_id = session_selector
else:
    sessions = orch.list_sessions()
    if not sessions:
        print("No sessions found.")
        sys.exit(1)
    session_id = sessions[0]['id']

session = orch.change_style(session_id, style_name=params["style_name"])
print(f"Style changed to: {session.style_name}")
for fmt, path in session.output_paths.items():
    if not path.startswith("ERROR"):
        print(f"  {fmt.upper()}: {path}")
`

	pyCmd := exec.Command("python3", "-c", pyScript, paramsFile)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	return pyCmd.Run()
}

func reExport(cmd *cobra.Command) error {
	sessionSelector := getSessionSelector()
	formats := parseCSV(editExport)

	params := map[string]any{
		"session_selector": sessionSelector,
		"formats":          formats,
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

orch = Orchestrator()
session_selector = params.get("session_selector", "")
if session_selector:
    session_id = session_selector
else:
    sessions = orch.list_sessions()
    if not sessions:
        print("No sessions found.")
        sys.exit(1)
    session_id = sessions[0]['id']

paths = orch.export_formats(session_id, params["formats"])
for fmt, path in paths.items():
    if path.startswith("ERROR"):
        print(f"  {fmt}: {path}")
    else:
        print(f"  {fmt.upper()}: {path}")
`

	pyCmd := exec.Command("python3", "-c", pyScript, paramsFile)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	return pyCmd.Run()
}

func getSessionSelector() string {
	return editSession
}
