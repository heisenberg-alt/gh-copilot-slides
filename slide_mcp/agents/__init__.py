"""
Agent framework for Slide Builder.

Provides the base Agent class, shared context, and result types
used by all specialized agents (Research, Curator, Style Recommender,
Editor, Orchestrator).
"""

from .base import Agent, AgentResult, ConversationContext
from .orchestrator import Orchestrator
from .researcher import ResearchAgent
from .curator import CuratorAgent
from .style_recommender import StyleRecommenderAgent
from .editor import EditorAgent

__all__ = [
    "Agent",
    "AgentResult",
    "ConversationContext",
    "Orchestrator",
    "ResearchAgent",
    "CuratorAgent",
    "StyleRecommenderAgent",
    "EditorAgent",
]
