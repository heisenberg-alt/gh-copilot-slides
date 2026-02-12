"""
Research Agent — fetches and synthesizes content from URLs, web searches, and local files.

Capabilities:
  - URL fetching with article extraction (trafilatura/beautifulsoup4)
  - Web search via DuckDuckGo (no API key needed)
  - Local file reading: .txt, .md, .pdf, .docx, .pptx
  - LLM-powered summarization and key point extraction
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .base import Agent, AgentResult, ConversationContext

logger = logging.getLogger("slide-builder.agents.researcher")


class ResearchAgent(Agent):
    """Gathers and synthesizes content from multiple sources."""

    name = "researcher"
    description = "Fetches content from URLs, web searches, and local files, then synthesizes key insights."

    def run(self, context: ConversationContext) -> AgentResult:
        self._log(f"Starting research on: {context.topic}")
        sources: list[dict[str, Any]] = []
        errors: list[str] = []

        # 1. Fetch URLs
        for url in context.urls:
            try:
                content = self._fetch_url(url)
                if content:
                    sources.append({
                        "type": "url",
                        "source": url,
                        "content": content[:8000],  # Limit per source
                    })
                    self._log(f"Fetched URL: {url} ({len(content)} chars)")
            except Exception as e:
                errors.append(f"URL fetch failed ({url}): {e}")
                self._log(f"URL fetch failed: {url} — {e}")

        # 2. Read local files
        for file_path in context.files:
            try:
                content = self._read_file(file_path)
                if content:
                    sources.append({
                        "type": "file",
                        "source": file_path,
                        "content": content[:8000],
                    })
                    self._log(f"Read file: {file_path} ({len(content)} chars)")
            except Exception as e:
                errors.append(f"File read failed ({file_path}): {e}")
                self._log(f"File read failed: {file_path} — {e}")

        # 3. Web search for additional context
        try:
            search_results = self._web_search(context.topic, max_results=5)
            if search_results:
                sources.append({
                    "type": "web_search",
                    "source": f"DuckDuckGo: {context.topic}",
                    "content": search_results,
                })
                self._log(f"Web search completed ({len(search_results)} chars)")
        except Exception as e:
            errors.append(f"Web search failed: {e}")
            self._log(f"Web search failed: {e}")

        if not sources:
            # Fall back to LLM knowledge only
            self._log("No external sources available, using LLM knowledge only")
            sources.append({
                "type": "llm_knowledge",
                "source": "LLM general knowledge",
                "content": f"Topic: {context.topic}. Purpose: {context.purpose}.",
            })

        # 4. Synthesize all sources with LLM
        try:
            research_bundle = self._synthesize(context, sources)
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Research synthesis failed: {e}",
                messages=errors,
            )

        return AgentResult(
            success=True,
            data=research_bundle,
            messages=[
                f"Researched {len(sources)} source(s)",
                *errors,
            ],
        )

    def _fetch_url(self, url: str) -> str:
        """Fetch and extract article content from a URL."""
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded, include_links=False, include_tables=True)
                if text:
                    return text
        except ImportError:
            pass

        # Fallback: httpx + beautifulsoup4
        import httpx
        from bs4 import BeautifulSoup

        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "SlideBuilder/1.0"})
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Try article or main content
        article = soup.find("article") or soup.find("main") or soup.find("body")
        if article:
            return article.get_text(separator="\n", strip=True)
        return soup.get_text(separator="\n", strip=True)

    def _read_file(self, file_path: str) -> str:
        """Read content from a local file (txt, md, pdf, docx, pptx)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix in (".txt", ".md", ".csv", ".json"):
            return path.read_text(encoding="utf-8")

        if suffix == ".pdf":
            return self._read_pdf(path)

        if suffix == ".docx":
            return self._read_docx(path)

        if suffix == ".pptx":
            return self._read_pptx(path)

        # Try reading as text
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _read_pdf(self, path: Path) -> str:
        """Extract text from a PDF file."""
        try:
            import pymupdf  # PyMuPDF
            doc = pymupdf.open(str(path))
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            raise ImportError("pymupdf is required for PDF reading. Install: pip install pymupdf")

    def _read_docx(self, path: Path) -> str:
        """Extract text from a DOCX file."""
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise ImportError("python-docx is required for DOCX reading. Install: pip install python-docx")

    def _read_pptx(self, path: Path) -> str:
        """Extract text from a PPTX file using the existing converter."""
        from ..ppt_converter import summarize_extraction
        return summarize_extraction(str(path), str(path.parent))

    def _web_search(self, query: str, max_results: int = 5) -> str:
        """Search the web using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return ""

            parts = []
            for r in results:
                parts.append(f"**{r.get('title', '')}**")
                parts.append(r.get("body", ""))
                parts.append(f"Source: {r.get('href', '')}")
                parts.append("")
            return "\n".join(parts)
        except ImportError:
            raise ImportError(
                "duckduckgo-search is required for web search. "
                "Install: pip install duckduckgo-search"
            )

    def _synthesize(
        self, context: ConversationContext, sources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Use LLM to synthesize all gathered sources into a research bundle."""
        # Build source summary for the LLM
        source_texts = []
        for i, src in enumerate(sources):
            source_texts.append(
                f"--- Source {i+1} ({src['type']}: {src['source']}) ---\n"
                f"{src['content'][:4000]}\n"
            )

        all_sources = "\n".join(source_texts)

        system_prompt = """You are a research analyst preparing material for a presentation.
Given the collected source material, synthesize it into a structured research bundle.

Return a JSON object with these fields:
{
  "title_suggestion": "Suggested presentation title",
  "key_themes": ["theme1", "theme2", ...],
  "key_facts": [
    {"fact": "...", "source": "...", "importance": "high|medium|low"},
    ...
  ],
  "statistics": [
    {"stat": "...", "context": "...", "source": "..."},
    ...
  ],
  "quotes": [
    {"quote": "...", "attribution": "...", "source": "..."},
    ...
  ],
  "sections": [
    {"heading": "...", "summary": "...", "key_points": ["...", "..."]},
    ...
  ],
  "audience_insights": "Brief analysis of what would resonate with the target audience",
  "narrative_arc": "Suggested flow: intro theme → body themes → conclusion theme"
}

Include 5-15 key facts, 3-5 statistics, 2-4 quotes, and 3-7 sections.
Prioritize accuracy and attribution. Mark facts by importance."""

        user_prompt = f"""Topic: {context.topic}
Purpose: {context.purpose}
Target audience: {context.audience or 'General'}
Target slide count: {context.slide_count}
Extra instructions: {context.extra_instructions or 'None'}

Collected source material:
{all_sources}"""

        result = self.llm.generate_json(system_prompt, user_prompt)

        # Attach raw sources for reference
        result["raw_sources"] = [
            {"type": s["type"], "source": s["source"], "length": len(s["content"])}
            for s in sources
        ]

        return result
