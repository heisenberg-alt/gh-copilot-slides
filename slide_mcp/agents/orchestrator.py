"""
Orchestrator — coordinates the 5-agent pipeline for research-driven presentations.

Pipeline phases:
  1. Input parsing → extract topic, URLs, files, preferences
  2. Research → Research Agent gathers and synthesizes content
  3. Curation → Curator Agent builds slide structure
  4. Style selection → Style Recommender Agent picks the best theme
  5. Generation → Export to HTML/PPTX/PDF via exporters
  6. Edit loop → Editor Agent handles iterative refinement
"""

from __future__ import annotations

import logging
from typing import Any

from .base import AgentResult, ConversationContext
from .researcher import ResearchAgent
from .curator import CuratorAgent
from .style_recommender import StyleRecommenderAgent
from .editor import EditorAgent
from ..llm import LLMClient, get_client
from ..session import PresentationSession, SessionManager

logger = logging.getLogger("slide-builder.orchestrator")


class Orchestrator:
    """Central coordinator managing the agent pipeline."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        workspace_dir: str = ".",
    ):
        self.llm = llm or get_client()
        self.session_manager = SessionManager(workspace_dir)

        # Initialize agents
        self.researcher = ResearchAgent(self.llm)
        self.curator = CuratorAgent(self.llm)
        self.style_recommender = StyleRecommenderAgent(self.llm)
        self.editor = EditorAgent(self.llm)

    def create_presentation(
        self,
        topic: str,
        urls: list[str] | None = None,
        files: list[str] | None = None,
        slide_count: int = 10,
        purpose: str = "presentation",
        mood: str = "",
        audience: str = "",
        style_name: str = "",
        pptx_template: str | None = None,
        output_dir: str = ".",
        output_formats: list[str] | None = None,
        extra_instructions: str = "",
    ) -> PresentationSession:
        """
        Run the full pipeline: research → curate → style → generate.

        Returns a PresentationSession with all results and output paths.
        """
        output_formats = output_formats or ["html"]

        # Build context
        context = ConversationContext(
            topic=topic,
            purpose=purpose,
            urls=urls or [],
            files=files or [],
            slide_count=slide_count,
            mood=mood,
            audience=audience,
            style_name=style_name,
            pptx_template_path=pptx_template,
            output_dir=output_dir,
            output_formats=output_formats,
            extra_instructions=extra_instructions,
        )

        # Create session
        session = self.session_manager.create(
            topic=topic,
            purpose=purpose,
            urls=urls or [],
            files=files or [],
            mood=mood,
            audience=audience,
            slide_count=slide_count,
            output_formats=output_formats,
        )

        logger.info(f"[orchestrator] Starting pipeline for session {session.id}: {topic}")

        # ── Phase 1: Research ────────────────────────────────────────────
        logger.info("[orchestrator] Phase 1: Research")
        research_result = self.researcher.run(context)
        if not research_result.success:
            logger.warning(f"[orchestrator] Research failed: {research_result.error}")
            # Continue with empty research — curator will use LLM knowledge
            context.research_data = {}
        else:
            context.research_data = research_result.data
            session.research_data = research_result.data

        # ── Phase 2: Curation ────────────────────────────────────────────
        logger.info("[orchestrator] Phase 2: Curation")
        curator_result = self.curator.run(context)
        if not curator_result.success:
            raise RuntimeError(f"Curation failed: {curator_result.error}")

        context.slides = curator_result.data["slides"]
        context.presentation_title = curator_result.data["presentation_title"]
        session.slides = context.slides
        session.presentation_title = context.presentation_title

        # ── Phase 3: Style Selection ─────────────────────────────────────
        logger.info("[orchestrator] Phase 3: Style Selection")
        style_result = self.style_recommender.run(context)
        if style_result.success:
            context.style_name = style_result.data.get("recommended_style", "bold_signal")
            context.style_recommendations = style_result.data.get("recommendations", [])
            if style_result.data.get("custom_preset"):
                context.custom_preset = style_result.data["custom_preset"]
                session.custom_preset = context.custom_preset
        else:
            context.style_name = context.style_name or "bold_signal"

        session.style_name = context.style_name

        # ── Phase 4: Export ──────────────────────────────────────────────
        logger.info("[orchestrator] Phase 4: Export")
        output_paths = self._export(context, session)
        session.output_paths = output_paths
        context.output_paths = output_paths

        # Save session
        self.session_manager.save(session)
        logger.info(f"[orchestrator] Pipeline complete. Session: {session.id}")

        return session

    def edit_presentation(
        self,
        session_id: str,
        instruction: str,
    ) -> PresentationSession:
        """
        Edit an existing presentation by session ID.

        Loads the session, applies the edit, regenerates outputs.
        """
        session = self.session_manager.load(session_id)

        # Build context from session
        context = ConversationContext(
            topic=session.topic,
            purpose=session.purpose,
            slides=session.slides,
            presentation_title=session.presentation_title,
            style_name=session.style_name,
            custom_preset=session.custom_preset,
            output_dir=session.output_paths.get("html", ".").rsplit("/", 1)[0] if session.output_paths else ".",
            output_formats=session.output_formats,
            research_data=session.research_data,
        )

        # Run editor
        context.edit_instruction = instruction
        edit_result = self.editor.run(context)
        if not edit_result.success:
            raise RuntimeError(f"Edit failed: {edit_result.error}")

        # Update session
        session.slides = edit_result.data["slides"]
        session.add_edit(instruction, edit_result.data.get("change_summary", ""))

        # Re-export
        context.slides = session.slides
        output_paths = self._export(context, session)
        session.output_paths = output_paths

        self.session_manager.save(session)
        logger.info(f"[orchestrator] Edit applied to session {session_id}")

        return session

    def change_style(
        self,
        session_id: str,
        style_name: str | None = None,
        pptx_template: str | None = None,
    ) -> PresentationSession:
        """Change the style of an existing presentation."""
        session = self.session_manager.load(session_id)

        if pptx_template:
            # Extract theme from PPTX template
            context = ConversationContext(
                pptx_template_path=pptx_template,
                style_name="",
            )
            style_result = self.style_recommender.run(context)
            if style_result.success and style_result.data.get("custom_preset"):
                session.custom_preset = style_result.data["custom_preset"]
                session.style_name = "custom"
        elif style_name:
            session.style_name = style_name
            session.custom_preset = None

        # Re-export
        context = ConversationContext(
            topic=session.topic,
            slides=session.slides,
            presentation_title=session.presentation_title,
            style_name=session.style_name,
            custom_preset=session.custom_preset,
            output_dir=session.output_paths.get("html", ".").rsplit("/", 1)[0] if session.output_paths else ".",
            output_formats=session.output_formats,
        )
        output_paths = self._export(context, session)
        session.output_paths = output_paths
        session.add_edit(
            f"Changed style to {style_name or 'custom PPTX template'}",
            f"Style updated to {session.style_name}",
        )

        self.session_manager.save(session)
        return session

    def export_formats(
        self,
        session_id: str,
        formats: list[str],
        output_dir: str = ".",
    ) -> dict[str, str]:
        """Export an existing session to additional formats."""
        session = self.session_manager.load(session_id)

        context = ConversationContext(
            topic=session.topic,
            slides=session.slides,
            presentation_title=session.presentation_title,
            style_name=session.style_name,
            custom_preset=session.custom_preset,
            output_dir=output_dir,
            output_formats=formats,
        )

        output_paths = self._export(context, session)
        session.output_paths.update(output_paths)
        session.output_formats = list(set(session.output_formats + formats))
        self.session_manager.save(session)
        return output_paths

    def _export(
        self, context: ConversationContext, session: PresentationSession
    ) -> dict[str, str]:
        """Run exporters for all requested formats."""
        from ..exporters import export_all

        return export_all(
            title=context.presentation_title or context.topic,
            slides=context.slides,
            style_name=context.style_name,
            custom_preset=context.custom_preset,
            output_dir=context.output_dir,
            formats=context.output_formats,
            pptx_template=context.pptx_template_path,
        )

    def research_only(
        self,
        topic: str,
        urls: list[str] | None = None,
        files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run only the Research Agent and return the research bundle."""
        context = ConversationContext(
            topic=topic,
            urls=urls or [],
            files=files or [],
        )
        result = self.researcher.run(context)
        if not result.success:
            raise RuntimeError(f"Research failed: {result.error}")
        return result.data

    def list_sessions(self) -> list[dict[str, str]]:
        """List all saved sessions."""
        return self.session_manager.list_sessions()

    def get_session(self, session_id: str) -> PresentationSession:
        """Load a specific session."""
        return self.session_manager.load(session_id)
