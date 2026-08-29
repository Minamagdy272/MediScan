"""
ReportLab Multi-Page PDF Generation Service.
Gated: Generated only for ACCEPT-approved reports.
"""

import re
import html
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from .config import REPORTS_DIR


def _pdf_header_footer(canvas, doc):
    """Adds a professional header and footer to every page."""
    canvas.saveState()
    width, height = A4

    # Header line
    canvas.setStrokeColor(colors.HexColor("#1F4E79"))
    canvas.setLineWidth(0.7)
    canvas.line(
        doc.leftMargin,
        height - 1.3 * cm,
        width - doc.rightMargin,
        height - 1.3 * cm
    )

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor("#1F4E79"))
    canvas.drawString(
        doc.leftMargin,
        height - 1.0 * cm,
        "MEDISCAN"
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(
        width - doc.rightMargin,
        height - 1.0 * cm,
        "Evidence-Grounded Clinical Decision Support"
    )

    # Footer line
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.setLineWidth(0.5)
    canvas.line(
        doc.leftMargin,
        1.3 * cm,
        width - doc.rightMargin,
        1.3 * cm
    )

    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)

    footer_text = (
        "MediScan Research Prototype — "
        "Not a substitute for licensed clinical judgment"
    )

    canvas.drawString(
        doc.leftMargin,
        0.9 * cm,
        footer_text
    )

    canvas.drawRightString(
        width - doc.rightMargin,
        0.9 * cm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


def _convert_inline_markdown(text: str) -> str:
    """Converts basic Markdown formatting into ReportLab-safe XML."""
    text = html.escape(text)
    # Bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"(?<!\*)\*(.*?)\*(?!\*)", r"<i>\1</i>", text)
    # Inline code
    text = re.sub(r"`(.*?)`", r'<font name="Courier">\1</font>', text)
    return text


def _extract_report_title(report_text: str) -> Tuple[str, list]:
    """Extracts the first H1 title from the generated response."""
    lines = report_text.strip().splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("# "):
            return line.strip()[2:].strip(), lines[i + 1:]
    return "MediScan Clinical Decision Support Report", lines


def generate_pdf_report(
    report_text: str,
    output_path: Optional[str] = None,
    *,
    session_id: Optional[str] = None,
    response_type: Optional[str] = None,
    final_action: Optional[str] = None,
    evidence_count: Optional[int] = None
) -> str:
    """Generate a professional multi-page PDF."""
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(
            REPORTS_DIR / f"MediScan_Report_{timestamp}.pdf"
        )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
        title="MediScan Clinical Decision Support Report",
        author="MediScan Agentic RAG System"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ProfessionalTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "ProfessionalSubtitle",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1F4E79"),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#2F5597"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.7,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=8,
        splitLongWords=True
    )

    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=16,
        firstLineIndent=-8,
        bulletIndent=4,
        spaceAfter=5
    )

    citation_style = ParagraphStyle(
        "Citation",
        parent=body_style,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#555555"),
        leftIndent=8,
        spaceBefore=4,
        spaceAfter=4
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=body_style,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#7F6000"),
        backColor=colors.HexColor("#FFF2CC"),
        borderColor=colors.HexColor("#D6B656"),
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=12,
        spaceAfter=10
    )

    title, lines = _extract_report_title(report_text)
    story = []

    # Title
    story.append(Paragraph(html.escape(title), title_style))
    story.append(Paragraph("Evidence-Grounded Agentic RAG Clinical Decision Support", subtitle_style))

    # Metadata
    metadata = [
        ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Session ID", session_id or "N/A"],
        ["Response Type", response_type or "N/A"],
        ["Final Policy Action", final_action or "N/A"],
        ["Evidence Records Used", str(evidence_count or 0)],
    ]

    metadata_table = Table(metadata, colWidths=[4.2 * cm, 11.8 * cm])
    metadata_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1F4E79")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D9E2F3")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(metadata_table)
    story.append(Spacer(1, 16))

    # Parse Lines
    paragraph_buffer = []

    def flush_paragraph_buffer():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            combined = " ".join(paragraph_buffer).strip()
            if combined:
                story.append(Paragraph(_convert_inline_markdown(combined), body_style))
        paragraph_buffer = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph_buffer()
            story.append(Spacer(1, 5))
            continue
        if line.startswith("# "):
            flush_paragraph_buffer()
            story.append(Paragraph(_convert_inline_markdown(line[2:]), h1_style))
            continue
        if line.startswith("## "):
            flush_paragraph_buffer()
            story.append(Paragraph(_convert_inline_markdown(line[3:]), h2_style))
            continue
        if line in ["---", "***", "___"]:
            flush_paragraph_buffer()
            story.append(Spacer(1, 8))
            continue
        if line.startswith("- ") or line.startswith("* "):
            flush_paragraph_buffer()
            story.append(Paragraph(_convert_inline_markdown(line[2:]), bullet_style, bulletText="•"))
            continue
        if re.match(r"^\[[^\]]+\]", line):
            flush_paragraph_buffer()
            story.append(Paragraph(_convert_inline_markdown(line), citation_style))
            continue
        if "disclaimer" in line.lower():
            flush_paragraph_buffer()
            story.append(Paragraph(_convert_inline_markdown(line), disclaimer_style))
            continue
        paragraph_buffer.append(line)

    flush_paragraph_buffer()
    doc.build(story, onFirstPage=_pdf_header_footer, onLaterPages=_pdf_header_footer)
    return output_path
