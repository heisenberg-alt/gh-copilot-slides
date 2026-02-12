package main

import (
	"fmt"
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

	pyScript := fmt.Sprintf(`
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(%q)))
from slide_mcp.agents.orchestrator import Orchestrator

orch = Orchestrator()
%s
session = orch.edit_presentation(session_id, %q)
print("Session: " + session.id)
print("Slides: " + str(len(session.slides)))
if session.edit_history:
    print("Changes: " + session.edit_history[-1].get('summary', 'Updated'))
for fmt, path in session.output_paths.items():
    if not path.startswith("ERROR"):
        print(f"  {fmt.upper()}: {path}")
`, ".", sessionSelector, editInstruction)

	pyCmd := exec.Command("python3", "-c", pyScript)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	if err := pyCmd.Run(); err != nil {
		return fmt.Errorf("edit failed: %w", err)
	}
	return nil
}

func editInteractive(cmd *cobra.Command) error {
	fmt.Println("\n  Slide Builder — Edit Mode")
	fmt.Println("  Commands: type edit instruction, 'style <name>', 'export <formats>', or 'done'\n")

	// Show current session info
	listPyScript := fmt.Sprintf(`
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(%q)))
from slide_mcp.agents.orchestrator import Orchestrator

orch = Orchestrator()
sessions = orch.list_sessions()
if not sessions:
    print("No sessions found. Create one with: slides research --topic 'Your Topic'")
else:
    s = sessions[0]
    print(f"Session: {s['id']} — {s.get('topic', 'Untitled')} ({s.get('slides', '0')} slides)")
`, ".")

	listCmd := exec.Command("python3", "-c", listPyScript)
	listCmd.Stdout = cmd.OutOrStdout()
	listCmd.Stderr = cmd.ErrOrStderr()
	listCmd.Run()

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

	pyScript := fmt.Sprintf(`
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(%q)))
from slide_mcp.agents.orchestrator import Orchestrator

orch = Orchestrator()
%s
session = orch.change_style(session_id, style_name=%q)
print(f"Style changed to: {session.style_name}")
for fmt, path in session.output_paths.items():
    if not path.startswith("ERROR"):
        print(f"  {fmt.upper()}: {path}")
`, ".", sessionSelector, editStyle)

	pyCmd := exec.Command("python3", "-c", pyScript)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	return pyCmd.Run()
}

func reExport(cmd *cobra.Command) error {
	sessionSelector := getSessionSelector()
	formats := parseCSV(editExport)
	formatsJSON := toJSONArray(formats)

	pyScript := fmt.Sprintf(`
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(%q)))
from slide_mcp.agents.orchestrator import Orchestrator

orch = Orchestrator()
%s
paths = orch.export_formats(session_id, %s)
for fmt, path in paths.items():
    if path.startswith("ERROR"):
        print(f"  {fmt}: {path}")
    else:
        print(f"  {fmt.upper()}: {path}")
`, ".", sessionSelector, formatsJSON)

	pyCmd := exec.Command("python3", "-c", pyScript)
	pyCmd.Stdout = cmd.OutOrStdout()
	pyCmd.Stderr = cmd.ErrOrStderr()

	return pyCmd.Run()
}

func getSessionSelector() string {
	if editSession != "" {
		return fmt.Sprintf("session_id = %q", editSession)
	}
	return `sessions = orch.list_sessions()
if not sessions:
    print("No sessions found.")
    sys.exit(1)
session_id = sessions[0]['id']`
}
