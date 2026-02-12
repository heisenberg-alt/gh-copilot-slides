"""
Base agent framework — shared types and abstract base class.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields as dataclass_fields
from typing import Any

from ..llm import LLMClient

logger = logging.getLogger("slide-builder.agents")


@dataclass
class AgentResult:
    """Result returned by an agent after execution."""
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class ConversationContext:
    """
    Shared context passed between agents in the orchestrator pipeline.

    Accumulates data as each agent runs: research results, curated slides,
    style choices, etc.
    """
    # User inputs
    topic: str = ""
    purpose: str = "presentation"
    urls: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    slide_count: int = 10
    mood: str = ""
    audience: str = ""
    extra_instructions: str = ""

    # Research Agent output
    research_data: dict[str, Any] = field(default_factory=dict)

    # Curator Agent output
    slides: list[dict[str, Any]] = field(default_factory=list)
    presentation_title: str = ""

    # Style Recommender output
    style_name: str = ""
    style_recommendations: list[dict[str, Any]] = field(default_factory=list)
    custom_preset: dict[str, Any] | None = None
    pptx_template_path: str | None = None

    # Output paths
    output_dir: str = "."
    output_formats: list[str] = field(default_factory=lambda: ["html"])
    output_paths: dict[str, str] = field(default_factory=dict)

    # Edit history
    edit_history: list[dict[str, Any]] = field(default_factory=list)

    # Editor instruction (set before calling EditorAgent.run)
    edit_instruction: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to a dict (for session persistence)."""
        return {
            "topic": self.topic,
            "purpose": self.purpose,
            "urls": self.urls,
            "files": self.files,
            "slide_count": self.slide_count,
            "mood": self.mood,
            "audience": self.audience,
            "extra_instructions": self.extra_instructions,
            "research_data": self.research_data,
            "slides": self.slides,
            "presentation_title": self.presentation_title,
            "style_name": self.style_name,
            "style_recommendations": self.style_recommendations,
            "custom_preset": self.custom_preset,
            "pptx_template_path": self.pptx_template_path,
            "output_dir": self.output_dir,
            "output_formats": self.output_formats,
            "output_paths": self.output_paths,
            "edit_history": self.edit_history,
            "edit_instruction": self.edit_instruction,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversationContext:
        """Deserialize context from a dict, only setting known dataclass fields."""
        ctx = cls()
        allowed = {f.name for f in dataclass_fields(cls)}
        for key, value in data.items():
            if key in allowed:
                setattr(ctx, key, value)
        return ctx


class Agent(ABC):
    """Abstract base class for all agents."""

    name: str = "base"
    description: str = ""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.logger = logging.getLogger(f"slide-builder.agents.{self.name}")

    @abstractmethod
    def run(self, context: ConversationContext) -> AgentResult:
        """Execute the agent's task using the shared context."""
        ...

    def _log(self, msg: str) -> None:
        self.logger.info(f"[{self.name}] {msg}")
