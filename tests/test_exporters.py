"""Tests for slide_mcp.exporters — export_all dispatch and safe filename."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slide_mcp.exporters import export_all


class TestExportAll:
    @patch("slide_mcp.exporters.export_html")
    def test_html_only(self, mock_html, sample_slides, tmp_output):
        mock_html.return_value = str(tmp_output / "test.html")
        result = export_all(
            title="Test",
            slides=sample_slides,
            style_name="bold_signal",
            output_dir=str(tmp_output),
            formats=["html"],
        )
        assert "html" in result
        mock_html.assert_called_once()

    @patch("slide_mcp.exporters.export_pptx")
    @patch("slide_mcp.exporters.export_html")
    def test_multiple_formats(self, mock_html, mock_pptx, sample_slides, tmp_output):
        mock_html.return_value = str(tmp_output / "test.html")
        mock_pptx.return_value = str(tmp_output / "test.pptx")
        result = export_all(
            title="Test",
            slides=sample_slides,
            style_name="bold_signal",
            output_dir=str(tmp_output),
            formats=["html", "pptx"],
        )
        assert "html" in result
        assert "pptx" in result

    def test_unknown_format_skipped(self, sample_slides, tmp_output):
        with patch("slide_mcp.exporters.export_html") as mock_html:
            mock_html.return_value = str(tmp_output / "test.html")
            result = export_all(
                title="Test",
                slides=sample_slides,
                style_name="bold_signal",
                output_dir=str(tmp_output),
                formats=["html", "docx"],
            )
            assert "html" in result
            assert "docx" not in result

    def test_safe_filename_generation(self, sample_slides, tmp_output):
        """Title with special chars should produce safe filename."""
        with patch("slide_mcp.exporters.export_html") as mock_html:
            mock_html.return_value = str(tmp_output / "test.html")
            export_all(
                title="My Deck! @#$ (2024)",
                slides=sample_slides,
                style_name="bold_signal",
                output_dir=str(tmp_output),
                formats=["html"],
            )
            # Check the output_path passed to export_html
            call_args = mock_html.call_args
            output_path = call_args[1].get("output_path") or call_args[0][3] if len(call_args[0]) > 3 else call_args[1]["output_path"]
            # Should not contain special chars
            filename = Path(output_path).stem
            assert "@" not in filename
            assert "!" not in filename

    def test_default_formats_is_html(self, sample_slides, tmp_output):
        with patch("slide_mcp.exporters.export_html") as mock_html:
            mock_html.return_value = str(tmp_output / "test.html")
            result = export_all(
                title="Test",
                slides=sample_slides,
                style_name="bold_signal",
                output_dir=str(tmp_output),
            )
            assert "html" in result

    @patch("slide_mcp.exporters.export_html")
    def test_export_error_captured(self, mock_html, sample_slides, tmp_output):
        mock_html.side_effect = RuntimeError("Template error")
        result = export_all(
            title="Test",
            slides=sample_slides,
            style_name="bold_signal",
            output_dir=str(tmp_output),
            formats=["html"],
        )
        assert "ERROR" in result["html"]
