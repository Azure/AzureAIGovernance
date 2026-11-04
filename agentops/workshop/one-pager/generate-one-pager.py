from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, KeepTogether, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "agentops-vbd-one-pager.md"
OUTPUT = ROOT / "agentops-vbd-one-pager.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 14 * mm
GUTTER = 8 * mm
HERO_HEIGHT = 49 * mm
INFO_HEIGHT = 17 * mm
CONTENT_TOP = PAGE_HEIGHT - HERO_HEIGHT - INFO_HEIGHT
CONTENT_BOTTOM = 13 * mm
COLUMN_WIDTH = (PAGE_WIDTH - (2 * MARGIN) - GUTTER) / 2

NAVY = colors.HexColor("#172A46")
BLUE = colors.HexColor("#244A76")
CYAN = colors.HexColor("#37B5D8")
MINT = colors.HexColor("#5DD6B5")
VIOLET = colors.HexColor("#8277E8")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#536273")
PALE = colors.HexColor("#EAF2F8")
WHITE = colors.white


def parse_source(path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata: dict[str, str] = {}
    sections: dict[str, list[str]] = {}

    index = 0
    if lines and lines[0] == "---":
        index = 1
        while index < len(lines) and lines[index] != "---":
            if ":" in lines[index]:
                key, value = lines[index].split(":", 1)
                metadata[key.strip()] = value.strip().strip('"')
            index += 1
        index += 1

    current_section: str | None = None
    for line in lines[index:]:
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections[current_section] = []
        elif current_section is not None:
            sections[current_section].append(line)

    return metadata, sections


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = escaped.replace("&lt;br/&gt;", "<br/>").replace(
        "&lt;br&gt;", "<br/>"
    )
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"\[(.+?)\]\((https?://.+?)\)",
        r'<link href="\2" color="#244A76"><u>\1</u></link>',
        escaped,
    )
    return escaped


BODY = ParagraphStyle(
    "Body",
    fontName="Helvetica",
    fontSize=8.8,
    leading=10.65,
    textColor=INK,
    alignment=TA_LEFT,
    spaceAfter=2.2 * mm,
)
SECTION = ParagraphStyle(
    "Section",
    parent=BODY,
    fontName="Helvetica-Bold",
    fontSize=11.8,
    leading=13.6,
    spaceBefore=1.1 * mm,
    spaceAfter=1.2 * mm,
)
SUBSECTION = ParagraphStyle(
    "Subsection",
    parent=BODY,
    fontName="Helvetica-Bold",
    fontSize=9.2,
    leading=10.8,
    spaceBefore=0.7 * mm,
    spaceAfter=0.4 * mm,
)
BULLET = ParagraphStyle(
    "Bullet",
    parent=BODY,
    leftIndent=3.5 * mm,
    firstLineIndent=-2.7 * mm,
    bulletIndent=0,
    spaceAfter=0.9 * mm,
)
NUMBERED = ParagraphStyle(
    "Numbered",
    parent=BULLET,
    leftIndent=4.2 * mm,
    firstLineIndent=-3.5 * mm,
)
CALLOUT = ParagraphStyle(
    "Callout",
    parent=BODY,
    fontName="Helvetica-Oblique",
    fontSize=8.2,
    leading=9.7,
    textColor=BLUE,
    borderColor=CYAN,
    borderWidth=0,
    borderPadding=(1.5 * mm, 2 * mm, 1.5 * mm, 3 * mm),
    backColor=PALE,
    spaceBefore=5.5 * mm,
    spaceAfter=3.5 * mm,
)
TABLE_HEADER = ParagraphStyle(
    "TableHeader",
    parent=BODY,
    fontName="Helvetica-Bold",
    fontSize=7.45,
    leading=8.55,
    textColor=WHITE,
)
TABLE_BODY = ParagraphStyle(
    "TableBody",
    parent=BODY,
    fontSize=7.25,
    leading=8.35,
    spaceAfter=0,
)
TABLE_LABEL = ParagraphStyle(
    "TableLabel",
    parent=TABLE_BODY,
    fontName="Helvetica-Bold",
    textColor=BLUE,
)
SCOPE_TABLE_BODY = ParagraphStyle(
    "ScopeTableBody",
    parent=BODY,
    spaceAfter=0,
)
SCOPE_TABLE_LABEL = ParagraphStyle(
    "ScopeTableLabel",
    parent=SCOPE_TABLE_BODY,
    fontName="Helvetica-Bold",
    textColor=BLUE,
)
SCOPE_TABLE_HEADER = ParagraphStyle(
    "ScopeTableHeader",
    parent=SCOPE_TABLE_LABEL,
    textColor=WHITE,
)
READINESS_BODY = ParagraphStyle(
    "ReadinessBody",
    parent=TABLE_BODY,
    fontSize=6.6,
    leading=7.5,
)
READINESS_LABEL = ParagraphStyle(
    "ReadinessLabel",
    parent=READINESS_BODY,
    fontName="Helvetica-Bold",
    textColor=BLUE,
)


def parse_blocks(lines: list[str]) -> list[tuple[str, object]]:
    blocks: list[tuple[str, object]] = []
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue

        if line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
            index += 1
            continue

        if line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                row = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                rows.append(row)
                index += 1
            if len(rows) >= 2:
                rows.pop(1)
            blocks.append(("table", rows))
            continue

        if line.startswith(">"):
            parts = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                parts.append(lines[index].strip()[1:].strip())
                index += 1
            blocks.append(("quote", " ".join(parts)))
            continue

        unordered = re.match(r"^- (.+)", line)
        if unordered:
            items = []
            while index < len(lines):
                item_line = lines[index].strip()
                match = re.match(r"^- (.+)", item_line)
                if not match:
                    break
                text = match.group(1)
                index += 1
                while (
                    index < len(lines)
                    and lines[index].strip()
                    and not re.match(r"^(?:- |\d+\. |### |\| |> )", lines[index].strip())
                ):
                    text += " " + lines[index].strip()
                    index += 1
                items.append(text)
            blocks.append(("ul", items))
            continue

        ordered = re.match(r"^(\d+)\. (.+)", line)
        if ordered:
            items = []
            while index < len(lines):
                item_line = lines[index].strip()
                match = re.match(r"^(\d+)\. (.+)", item_line)
                if not match:
                    break
                text = match.group(2)
                index += 1
                while (
                    index < len(lines)
                    and lines[index].strip()
                    and not re.match(r"^(?:- |\d+\. |### |\| |> )", lines[index].strip())
                ):
                    text += " " + lines[index].strip()
                    index += 1
                items.append(text)
            blocks.append(("ol", items))
            continue

        parts = [line]
        index += 1
        while index < len(lines):
            next_line = lines[index].strip()
            if not next_line or re.match(r"^(?:### |- |\d+\. |\| |> )", next_line):
                break
            parts.append(next_line)
            index += 1
        blocks.append(("p", " ".join(parts)))

    return blocks


def section_story(name: str, lines: list[str]) -> list[object]:
    story: list[object] = [Paragraph(inline_markup(name), SECTION)]

    for kind, value in parse_blocks(lines):
        if kind == "h3":
            story.append(Paragraph(inline_markup(str(value)), SUBSECTION))
        elif kind == "p":
            story.append(Paragraph(inline_markup(str(value)), BODY))
        elif kind == "quote":
            story.append(Paragraph(inline_markup(str(value)), CALLOUT))
        elif kind == "ul":
            for item in value:
                story.append(Paragraph(inline_markup(item), BULLET, bulletText="•"))
        elif kind == "ol":
            for number, item in enumerate(value, start=1):
                story.append(
                    Paragraph(inline_markup(item), NUMBERED, bulletText=f"{number}.")
                )
        elif kind == "table":
            rows = value
            is_scope_table = name == "Scope"
            is_readiness_table = rows[0][0] == "Area"
            is_access_table = rows[0][0] == "Identity"
            is_grouped_table = is_readiness_table or is_access_table
            table_data = []
            for row_index, row in enumerate(rows):
                table_row = []
                for column_index, cell in enumerate(row):
                    if row_index == 0:
                        style = SCOPE_TABLE_HEADER if is_scope_table else TABLE_HEADER
                    elif is_scope_table:
                        style = (
                            SCOPE_TABLE_LABEL if column_index == 0 else SCOPE_TABLE_BODY
                        )
                    elif is_grouped_table and column_index == 0:
                        style = READINESS_LABEL
                    elif is_grouped_table:
                        style = READINESS_BODY
                    else:
                        style = TABLE_BODY
                    table_row.append(Paragraph(inline_markup(cell), style))
                table_data.append(table_row)
            table = Table(
                table_data,
                colWidths=(
                    [25 * mm, COLUMN_WIDTH - (25 * mm)]
                    if len(rows[0]) == 2
                    else [21 * mm, 27 * mm, COLUMN_WIDTH - (48 * mm)]
                    if is_access_table
                    else [22 * mm, 30 * mm, COLUMN_WIDTH - (52 * mm)]
                ),
                repeatRows=1,
                hAlign="LEFT",
            )
            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F7FA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D5DF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.1 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.1 * mm),
            ]
            if is_scope_table:
                table_style.extend(
                    [
                        ("BACKGROUND", (0, 1), (0, -1), PALE),
                        ("BACKGROUND", (1, 1), (-1, -1), WHITE),
                    ]
                )
            if is_grouped_table:
                table_style.extend(
                    [
                        ("TOPPADDING", (0, 1), (-1, -1), 0.7 * mm),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 0.7 * mm),
                    ]
                )
                group_start = 1
                for row_index in range(2, len(rows) + 1):
                    group_ended = (
                        row_index == len(rows)
                        or rows[row_index][0] != rows[group_start][0]
                    )
                    if group_ended:
                        group_end = row_index - 1
                        if group_end > group_start:
                            table_style.append(
                                ("SPAN", (0, group_start), (0, group_end))
                            )
                        group_start = row_index
            table.setStyle(TableStyle(table_style))
            story.extend([table, Spacer(1, 1.3 * mm)])

    return story


def draw_agentops_hero(pdf: canvas.Canvas, metadata: dict[str, str]) -> None:
    y = PAGE_HEIGHT - HERO_HEIGHT
    pdf.setFillColor(NAVY)
    pdf.rect(0, y, PAGE_WIDTH, HERO_HEIGHT, stroke=0, fill=1)

    pdf.saveState()
    pdf.setStrokeColor(colors.HexColor("#49627F"))
    pdf.setLineWidth(0.7)
    nodes = [
        (126 * mm, y + 14 * mm, 5 * mm, CYAN),
        (151 * mm, y + 31 * mm, 6 * mm, MINT),
        (178 * mm, y + 20 * mm, 5.5 * mm, VIOLET),
        (194 * mm, y + 40 * mm, 4 * mm, CYAN),
        (117 * mm, y + 39 * mm, 3.5 * mm, VIOLET),
    ]
    connections = [(0, 1), (1, 2), (2, 3), (1, 4), (4, 0), (0, 2)]
    for start, end in connections:
        pdf.line(nodes[start][0], nodes[start][1], nodes[end][0], nodes[end][1])
    for x, node_y, radius, color in nodes:
        pdf.setFillColor(color)
        pdf.circle(x, node_y, radius, stroke=0, fill=1)
        pdf.setFillColor(NAVY)
        pdf.circle(x, node_y, radius * 0.42, stroke=0, fill=1)
    pdf.restoreState()

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawString(MARGIN, y + 26 * mm, "Workshop: AgentOps")
    pdf.setFont("Helvetica", 8.4)
    pdf.setFillColor(colors.HexColor("#AFC4D7"))
    pdf.drawString(MARGIN, y + 17 * mm, metadata.get("subtitle", ""))


def draw_information_band(pdf: canvas.Canvas, metadata: dict[str, str]) -> None:
    y = CONTENT_TOP
    pdf.setFillColor(BLUE)
    pdf.rect(0, y, PAGE_WIDTH, INFO_HEIGHT, stroke=0, fill=1)

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(MARGIN, y + 6.2 * mm, "Workshop")

    label_x = PAGE_WIDTH / 2 + 7 * mm
    value_x = label_x + 20 * mm
    entries = [
        ("Duration:", metadata.get("duration", "")),
        ("Structure:", metadata.get("structure", "")),
        ("Difficulty:", metadata.get("difficulty", "")),
        ("Format:", metadata.get("delivery", "")),
    ]
    for row, (label, value) in enumerate(entries):
        baseline = y + (12.8 - row * 3.5) * mm
        pdf.setFont("Helvetica-Bold", 7.8)
        pdf.drawString(label_x, baseline, label)
        pdf.setFont("Helvetica", 7.8)
        pdf.drawString(value_x, baseline, value)


def draw_footer(pdf: canvas.Canvas) -> None:
    pdf.setStrokeColor(colors.HexColor("#D7E0E8"))
    pdf.setLineWidth(0.5)
    pdf.line(MARGIN, 9.8 * mm, PAGE_WIDTH - MARGIN, 9.8 * mm)
    pdf.setFont("Helvetica", 6.7)
    pdf.setFillColor(MUTED)
    pdf.drawString(MARGIN, 6.4 * mm, "AI Governance Value Based Delivery")
    footer = "AgentOps | Microsoft Foundry"
    pdf.drawRightString(PAGE_WIDTH - MARGIN, 6.4 * mm, footer)


def add_column(
    pdf: canvas.Canvas,
    x: float,
    section_names: list[str],
    sections: dict[str, list[str]],
    section_gap: float = 5.5 * mm,
) -> None:
    story: list[object] = []
    for index, name in enumerate(section_names):
        if index:
            story.append(Spacer(1, section_gap))
        story.extend(section_story(name, sections[name]))

    frame = Frame(
        x,
        CONTENT_BOTTOM,
        COLUMN_WIDTH,
        CONTENT_TOP - CONTENT_BOTTOM - 4 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=2.5 * mm,
        bottomPadding=0,
        showBoundary=0,
    )
    frame.addFromList(story, pdf)
    if story:
        raise RuntimeError(
            f"Content overflow in column beginning with {section_names[0]!r}. "
            "Shorten the Markdown content or adjust the layout."
        )


def generate() -> None:
    metadata, sections = parse_source(SOURCE)
    left_sections = [
        "Description",
        "Audience",
        "Outcomes",
        "Format",
        "Prerequisites",
    ]
    right_sections = [
        "Scope",
        "Methodology",
        "Agenda",
        "Workshop materials",
        "Optional advanced module",
    ]
    required_sections = set(left_sections + right_sections)
    missing = required_sections.difference(sections)
    if missing:
        raise ValueError(f"Missing required sections: {', '.join(sorted(missing))}")
    unrendered = set(sections).difference(required_sections)
    if unrendered:
        raise ValueError(f"Unrendered sections: {', '.join(sorted(unrendered))}")

    pdf = canvas.Canvas(str(OUTPUT), pagesize=A4)
    pdf.setTitle(metadata.get("title", "AgentOps Value Based Delivery Workshop"))
    pdf.setAuthor("Azure AI Governance")
    pdf.setSubject("AgentOps Value Based Delivery workshop one-pager")

    draw_agentops_hero(pdf, metadata)
    draw_information_band(pdf, metadata)
    draw_footer(pdf)

    add_column(
        pdf,
        MARGIN,
        left_sections,
        sections,
        section_gap=13 * mm,
    )
    add_column(
        pdf,
        MARGIN + COLUMN_WIDTH + GUTTER,
        right_sections,
        sections,
        section_gap=8.8 * mm,
    )

    pdf.showPage()
    pdf.save()
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    generate()
