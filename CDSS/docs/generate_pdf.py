"""
CDSS Project – Full Architecture & Documentation PDF Generator
Run: python generate_pdf.py
Output: CDSS_Project_Documentation.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, PageTemplate
import datetime

# ── Colour Palette ────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#050d1a")
BLUE      = colors.HexColor("#3b82f6")
CYAN      = colors.HexColor("#06b6d4")
EMERALD   = colors.HexColor("#10b981")
AMBER     = colors.HexColor("#f59e0b")
RED       = colors.HexColor("#ef4444")
PURPLE    = colors.HexColor("#8b5cf6")
DARK_BLUE = colors.HexColor("#0f172a")
SLATE     = colors.HexColor("#1e293b")
LIGHT_BG  = colors.HexColor("#f0f6ff")
MID_GRAY  = colors.HexColor("#94a3b8")
DARK_GRAY = colors.HexColor("#334155")
WHITE     = colors.white
BLACK     = colors.black

OUTPUT_FILE = "CDSS_Project_Documentation.pdf"

# ── Page Size ─────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4  # 595 × 842 pt
MARGIN        = 2.2 * cm

# ─────────────────────────────────────────────────────────────────────────────
# Header / Footer Canvas Callback
# ─────────────────────────────────────────────────────────────────────────────
def header_footer(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 40, PAGE_W, 40, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, PAGE_H - 43, PAGE_W, 3, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN, PAGE_H - 28, "CDSS  ·  Clinical Decision Support System")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 28,
                           f"Project Architecture & Technical Documentation  ·  {datetime.date.today().strftime('%d %b %Y')}")
    # Footer bar
    canvas.setFillColor(SLATE)
    canvas.rect(0, 0, PAGE_W, 28, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, 28, PAGE_W, 2, fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(MARGIN, 10, "Confidential — For Internal Use Only")
    canvas.drawCentredString(PAGE_W / 2, 10, f"Page {doc.page}")
    canvas.drawRightString(PAGE_W - MARGIN, 10, "CDSS v1.0.0")
    canvas.restoreState()

# Cover page callback (no header/footer)
def cover_page_cb(canvas, doc):
    canvas.saveState()
    # Full-page navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Top accent bar
    canvas.setFillColor(BLUE)
    canvas.rect(0, PAGE_H - 8, PAGE_W, 8, fill=1, stroke=0)
    # Bottom accent bar
    canvas.setFillColor(BLUE)
    canvas.rect(0, 0, PAGE_W, 6, fill=1, stroke=0)
    # Decorative circle
    canvas.setFillColor(colors.HexColor("#1e3a5f"))
    canvas.circle(PAGE_W - 60, PAGE_H - 60, 90, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0f2a4a"))
    canvas.circle(60, 100, 70, fill=1, stroke=0)
    # Title
    canvas.setFont("Helvetica-Bold", 36)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 120, "CDSS")
    canvas.setFont("Helvetica", 18)
    canvas.setFillColor(colors.HexColor("#93c5fd"))
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 85, "Clinical Decision Support System")
    # Divider
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(2)
    canvas.line(MARGIN, PAGE_H / 2 + 70, PAGE_W - MARGIN, PAGE_H / 2 + 70)
    # Subtitle
    canvas.setFont("Helvetica", 13)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 45,
                             "Full Project Architecture & Technical Documentation")
    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 22,
                             "Frontend  ·  Backend  ·  AI Engine  ·  Database  ·  Workflow")
    # Version / date block
    canvas.setFillColor(colors.HexColor("#0f172a"))
    canvas.roundRect(MARGIN, PAGE_H / 2 - 60, PAGE_W - 2 * MARGIN, 70, 10, fill=1, stroke=0)
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(1)
    canvas.roundRect(MARGIN, PAGE_H / 2 - 60, PAGE_W - 2 * MARGIN, 70, 10, fill=0, stroke=1)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(BLUE)
    canvas.drawString(MARGIN + 20, PAGE_H / 2 - 15, "Version:")
    canvas.drawString(MARGIN + 140, PAGE_H / 2 - 15, "Date:")
    canvas.drawString(MARGIN + 260, PAGE_H / 2 - 15, "Stack:")
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN + 20, PAGE_H / 2 - 33, "1.0.0")
    canvas.drawString(MARGIN + 140, PAGE_H / 2 - 33, datetime.date.today().strftime('%d %B %Y'))
    canvas.drawString(MARGIN + 260, PAGE_H / 2 - 33, "React · FastAPI · SQLite · OpenRouter AI")
    canvas.restoreState()

# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    styles = {}
    styles["h1"] = ps("h1",
        fontName="Helvetica-Bold", fontSize=22, textColor=WHITE,
        backColor=DARK_BLUE, borderPad=10,
        spaceAfter=14, spaceBefore=6,
        leading=28, leftIndent=-MARGIN, rightIndent=-MARGIN,
        firstLineIndent=0
    )
    styles["h2"] = ps("h2",
        fontName="Helvetica-Bold", fontSize=15, textColor=BLUE,
        spaceBefore=18, spaceAfter=8, leading=20
    )
    styles["h3"] = ps("h3",
        fontName="Helvetica-Bold", fontSize=12, textColor=DARK_BLUE,
        spaceBefore=12, spaceAfter=5, leading=16,
        borderPad=4
    )
    styles["h4"] = ps("h4",
        fontName="Helvetica-Bold", fontSize=10, textColor=DARK_GRAY,
        spaceBefore=8, spaceAfter=3, leading=14
    )
    styles["body"] = ps("body",
        fontName="Helvetica", fontSize=9.5, textColor=DARK_GRAY,
        spaceAfter=5, leading=15, alignment=TA_JUSTIFY
    )
    styles["bullet"] = ps("bullet",
        fontName="Helvetica", fontSize=9.5, textColor=DARK_GRAY,
        spaceAfter=3, leading=14, leftIndent=14, bulletIndent=4,
        bulletText="•"
    )
    styles["code"] = ps("code",
        fontName="Courier", fontSize=8.5, textColor=colors.HexColor("#1e40af"),
        backColor=colors.HexColor("#eff6ff"), borderColor=colors.HexColor("#bfdbfe"),
        borderWidth=1, borderPad=6,
        spaceAfter=6, spaceBefore=4, leading=13
    )
    styles["caption"] = ps("caption",
        fontName="Helvetica-Oblique", fontSize=8, textColor=MID_GRAY,
        alignment=TA_CENTER, spaceAfter=8
    )
    styles["label"] = ps("label",
        fontName="Helvetica-Bold", fontSize=8, textColor=BLUE
    )
    styles["note"] = ps("note",
        fontName="Helvetica-Oblique", fontSize=9, textColor=colors.HexColor("#92400e"),
        backColor=colors.HexColor("#fef3c7"), borderColor=AMBER, borderWidth=1, borderPad=6,
        spaceAfter=8, leading=14
    )
    styles["toc_h1"] = ps("toc_h1",
        fontName="Helvetica-Bold", fontSize=10, textColor=DARK_BLUE,
        spaceAfter=4, leading=14
    )
    styles["toc_h2"] = ps("toc_h2",
        fontName="Helvetica", fontSize=9, textColor=DARK_GRAY,
        spaceAfter=2, leftIndent=14, leading=13
    )
    return styles


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def section_header(title, styles, color=BLUE):
    return [
        HRFlowable(width="100%", thickness=2, color=color, spaceAfter=4, spaceBefore=16),
        Paragraph(title, styles["h2"]),
    ]

def sub_header(title, styles):
    return Paragraph(title, styles["h3"])

def body(text, styles):
    return Paragraph(text, styles["body"])

def bullet_item(text, styles):
    return Paragraph(text, styles["bullet"])

def code_block(text, styles):
    return Paragraph(text.replace("\n", "<br/>"), styles["code"])

def sp(n=8):
    return Spacer(1, n)

def colored_table(data, col_widths, header_bg=BLUE, row_alt=colors.HexColor("#f8fafc")):
    t = Table(data, colWidths=col_widths)
    style = TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  header_bg),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  9),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR",   (0, 1), (-1, -1), DARK_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, row_alt]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0,0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWHEIGHT",   (0, 0), (0, 0),   22),
    ])
    t.setStyle(style)
    return t

def info_box(text, styles, bg=colors.HexColor("#eff6ff"), border=BLUE):
    s = ParagraphStyle("infobox",
        fontName="Helvetica", fontSize=9, textColor=DARK_GRAY,
        backColor=bg, borderColor=border, borderWidth=1.2, borderPad=8,
        spaceAfter=10, leading=14, alignment=TA_LEFT
    )
    return Paragraph(text, s)

def badge_table(items, bg_color, text_color=WHITE):
    """Render a row of coloured badge chips."""
    row = []
    for item in items:
        cell = Paragraph(item, ParagraphStyle("badge",
            fontName="Helvetica-Bold", fontSize=8, textColor=text_color,
            alignment=TA_CENTER))
        row.append(cell)
    t = Table([row], colWidths=[None] * len(items))
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), bg_color),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",(0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6, 6, 6, 6]),
    ]))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# ASCII Architecture Diagram (drawn via Table)
# ─────────────────────────────────────────────────────────────────────────────
def arch_diagram(styles):
    """Return a Table that renders a clean architecture diagram."""
    cell_style = ParagraphStyle("cell",
        fontName="Helvetica-Bold", fontSize=9, textColor=WHITE,
        alignment=TA_CENTER, leading=13
    )
    sub_style = ParagraphStyle("sub",
        fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#dbeafe"),
        alignment=TA_CENTER, leading=11
    )
    arrow_style = ParagraphStyle("arrow",
        fontName="Helvetica-Bold", fontSize=14, textColor=BLUE,
        alignment=TA_CENTER
    )

    def box(title, sub, bg):
        return [Paragraph(title, cell_style), Paragraph(sub, sub_style)], bg

    rows = [
        # Row 1 – User
        [None, ([Paragraph("👤  CLINICIAN / DOCTOR", cell_style),
                 Paragraph("Browser: Chrome / Edge / Firefox", sub_style)], colors.HexColor("#1e3a5f")),
         None],
        # Arrow down
        [None, ([Paragraph("⬇  HTTPS / REST API", arrow_style)], None), None],
        # Row 2 – Frontend
        [([Paragraph("Home Page", cell_style), Paragraph("Landing + CTA", sub_style)], colors.HexColor("#1d4ed8")),
         ([Paragraph("Consultation Page", cell_style), Paragraph("AI Diagnostic Form", sub_style)], colors.HexColor("#1d4ed8")),
         ([Paragraph("Patient History", cell_style), Paragraph("Records Archive", sub_style)], colors.HexColor("#1d4ed8"))],
        # Row frontend continued
        [([Paragraph("Dashboard", cell_style), Paragraph("Metrics + Charts", sub_style)], colors.HexColor("#1e40af")),
         ([Paragraph("Diagnostic Results", cell_style), Paragraph("Save to DB flow", sub_style)], colors.HexColor("#1e40af")),
         ([Paragraph("Results (History)", cell_style), Paragraph("View saved record", sub_style)], colors.HexColor("#1e40af"))],
        # Arrow
        [None, ([Paragraph("⬇  HTTP POST/GET  →  FastAPI  (port 8000)", arrow_style)], None), None],
        # Row 3 – Backend
        [([Paragraph("POST /extract", cell_style), Paragraph("NLP Text → Structured Data", sub_style)], colors.HexColor("#065f46")),
         ([Paragraph("POST /predict", cell_style), Paragraph("AI Differential Diagnosis", sub_style)], colors.HexColor("#065f46")),
         ([Paragraph("GET|POST /patient/*", cell_style), Paragraph("History + Save", sub_style)], colors.HexColor("#065f46"))],
        # Arrow
        [None, ([Paragraph("⬇  LLM Cascade", arrow_style)], None), None],
        # Row 4 – AI Layer
        [([Paragraph("OpenRouter API", cell_style), Paragraph("Primary: Gemma 4 26B", sub_style)], colors.HexColor("#6d28d9")),
         ([Paragraph("Local Ollama", cell_style), Paragraph("Fallback: Gemma2 2B", sub_style)], colors.HexColor("#4c1d95")),
         ([Paragraph("Rule Engine", cell_style), Paragraph("Offline Hard Fallback", sub_style)], colors.HexColor("#3b0764"))],
        # Arrow
        [None, ([Paragraph("⬇  SQLAlchemy ORM", arrow_style)], None), None],
        # Row 5 – DB
        [None, ([Paragraph("SQLite  (cdss.db)", cell_style),
                 Paragraph("Consultations Table  ·  Patient Records", sub_style)], colors.HexColor("#92400e")),
         None],
    ]

    FULL_W = PAGE_W - 2 * MARGIN
    COL_W  = [FULL_W / 3] * 3

    table_rows = []
    for row in rows:
        cells = []
        bgs   = []
        spans = False
        if row[0] is None and row[2] is None:
            # Center spanning cell
            content, bg = row[1]
            cells = ["", content, ""]
            bgs   = [None, bg, None]
            spans = True
        else:
            for item in row:
                if item is None:
                    cells.append("")
                    bgs.append(None)
                else:
                    content, bg = item
                    cells.append(content)
                    bgs.append(bg)
        table_rows.append((cells, bgs, spans))

    flat_rows = [r[0] for r in table_rows]
    t = Table(flat_rows, colWidths=COL_W, rowHeights=None)
    ts = TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0,0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
    ])
    for i, (_, bgs, spans) in enumerate(table_rows):
        if spans:
            ts.add("SPAN",      (0, i), (2, i))
            ts.add("ALIGN",     (0, i), (2, i), "CENTER")
        for j, bg in enumerate(bgs):
            if bg:
                ts.add("BACKGROUND", (j, i), (j, i), bg)
                ts.add("TEXTCOLOR",  (j, i), (j, i), WHITE)
        if not spans:
            ts.add("GRID", (0, i), (-1, i), 0.5, colors.HexColor("#1e293b"))
    t.setStyle(ts)
    return t

# ─────────────────────────────────────────────────────────────────────────────
# Build Content
# ─────────────────────────────────────────────────────────────────────────────
def build_story(styles):
    from reportlab.platypus import NextPageTemplate
    story = []

    # ── Cover Page: switch to cover template, add a minimal spacer, then switch back
    story.append(NextPageTemplate("cover"))
    story.append(PageBreak())   # triggers cover_page_cb on page 1
    story.append(NextPageTemplate("normal"))

    # ── TABLE OF CONTENTS ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Table of Contents", styles["h1"]))
    story.append(sp(12))

    toc = [
        ("1", "Project Overview"),
        ("  1.1", "Purpose & Goals"),
        ("  1.2", "Key Features"),
        ("  1.3", "Technology Stack Summary"),
        ("2", "System Architecture"),
        ("  2.1", "High-Level Architecture Diagram"),
        ("  2.2", "Component Interaction Flow"),
        ("3", "Frontend"),
        ("  3.1", "Tech Stack & Configuration"),
        ("  3.2", "Page Breakdown"),
        ("  3.3", "Design System & Styling"),
        ("  3.4", "State Management & Data Flow"),
        ("4", "Backend"),
        ("  4.1", "FastAPI Server"),
        ("  4.2", "API Endpoints"),
        ("  4.3", "Request / Response Schemas"),
        ("  4.4", "Middleware & CORS"),
        ("5", "AI & Machine Learning Engine"),
        ("  5.1", "AI Pipeline Overview"),
        ("  5.2", "OpenRouter API (Primary)"),
        ("  5.3", "Local Ollama / Gemma2 (Fallback)"),
        ("  5.4", "Rule-Based Engine (Offline Fallback)"),
        ("  5.5", "NLP Extraction Logic"),
        ("  5.6", "Prompt Engineering"),
        ("  5.7", "Disease Knowledge Base"),
        ("6", "Database"),
        ("  6.1", "Database Engine & ORM"),
        ("  6.2", "Schema & Models"),
        ("  6.3", "CRUD Operations"),
        ("  6.4", "Client-Side Fallback Storage"),
        ("7", "Red Flag Detection Engine"),
        ("8", "NHM Treatment Protocol (RAG)"),
        ("9", "End-to-End Workflow"),
        ("  9.1", "Consultation Workflow"),
        ("  9.2", "Data Save Workflow"),
        ("  9.3", "Patient History Workflow"),
        ("10","Environment & Configuration"),
        ("11","Security Considerations"),
        ("12","Known Limitations & Roadmap"),
    ]

    for num, title in toc:
        indent = 20 if num.startswith("  ") else 0
        s = styles["toc_h2"] if indent else styles["toc_h1"]
        story.append(Paragraph(
            f"<font color='#{BLUE.hexval()[2:]}'>{num.strip()}</font>&nbsp;&nbsp;&nbsp;{title}",
            s
        ))
    story.append(PageBreak())

    # ── 1. PROJECT OVERVIEW ──────────────────────────────────────────────────
    story += section_header("1.  Project Overview", styles)
    story.append(body(
        "The <b>Clinical Decision Support System (CDSS)</b> is a full-stack, AI-powered "
        "web application designed to assist clinicians and healthcare practitioners in "
        "making faster, more accurate diagnostic decisions at the point of care. "
        "Built for Indian primary health settings, it integrates with the National Health "
        "Mission (NHM) treatment protocols and provides real-time differential diagnoses, "
        "emergency red-flag alerts, and evidence-based treatment recommendations.", styles))
    story.append(sp())

    # 1.1
    story.append(sub_header("1.1  Purpose & Goals", styles))
    for b in [
        "<b>Goal 1 – AI Differential Diagnosis:</b> Given patient symptoms, vitals, and free-text clinical notes, produce a ranked list of up to 5 probable diagnoses with confidence scores.",
        "<b>Goal 2 – NLP Extraction:</b> Parse unstructured clinical free-text into structured data fields (age, sex, symptoms, vitals, duration).",
        "<b>Goal 3 – Red-Flag Detection:</b> Instantly alert clinicians to life-threatening conditions such as meningitis, ACS, shock, and hypoxia.",
        "<b>Goal 4 – NHM Treatment Guidelines:</b> Retrieve and display evidence-based drug dosage and referral instructions aligned with the National Health Mission.",
        "<b>Goal 5 – Patient Record Management:</b> Save, retrieve, and filter patient diagnostic history in an SQLite database.",
    ]:
        story.append(bullet_item(b, styles))
    story.append(sp())

    # 1.2
    story.append(sub_header("1.2  Key Features", styles))
    feat_data = [
        ["Feature", "Description"],
        ["AI Cascade Inference", "Primary → OpenRouter (Gemma 4 26B) → Local Ollama (Gemma2 2B) → Rule Engine"],
        ["Free-Text NLP", "Clinical notes parsed to extract symptoms, vitals, demographics via LLM + regex"],
        ["Differential Diagnosis", "Up to 5 ranked diagnoses with confidence % and SHAP-style explanatory features"],
        ["Red Flag Alerts", "Rule-based vital sign & symptom checks triggering emergency warnings"],
        ["NHM Treatment RAG", "Knowledge-base lookup returning NHM-aligned drug, dosage & referral data"],
        ["Patient History", "SQLite persistence with localStorage fallback; search, filter by status"],
        ["Responsive UI", "Liquid-glass design system; works on desktop & mobile; dark mode only"],
        ["Offline Fallback", "Full rule-based pipeline works without any external AI API"],
    ]
    story.append(colored_table(feat_data,
        [4.5*cm, 11.5*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 1.3
    story.append(sub_header("1.3  Technology Stack Summary", styles))
    stack_data = [
        ["Layer", "Technology", "Version / Notes"],
        ["Frontend Framework", "React + TypeScript", "v19.x  (Vite build)"],
        ["Frontend Routing",   "React Router DOM",   "v7.x"],
        ["Frontend Charts",    "Recharts",           "v3.x"],
        ["Frontend Icons",     "Lucide React",       "v1.x"],
        ["Frontend Animations","Framer Motion",      "v12.x"],
        ["Backend Framework",  "FastAPI",            "≥0.111  (Python 3.x)"],
        ["ASGI Server",        "Uvicorn",            "≥0.29 with standard extras"],
        ["Data Validation",    "Pydantic",           "v2.x"],
        ["ORM",                "SQLAlchemy",         "v2.x"],
        ["Database (default)", "SQLite",             "File: cdss.db"],
        ["Database (optional)","PostgreSQL",         "Via psycopg2-binary"],
        ["AI Primary",         "OpenRouter API",     "Model: google/gemma-4-26b-a4b-it:free"],
        ["AI Fallback 1",      "Ollama (local)",     "Model: gemma2:2b  @ localhost:11434"],
        ["AI Fallback 2",      "Rule-based engine",  "Pure Python, no external dependencies"],
        ["Build Tool",         "Vite",               "v8.x"],
        ["HTTP Client (BE)",   "requests",           "≥2.31"],
        ["Environment",        "python-dotenv",      "≥1.0"],
    ]
    story.append(colored_table(stack_data,
        [4.0*cm, 5.5*cm, 6.5*cm], header_bg=DARK_BLUE))
    story.append(PageBreak())

    # ── 2. SYSTEM ARCHITECTURE ───────────────────────────────────────────────
    story += section_header("2.  System Architecture", styles)

    # 2.1
    story.append(sub_header("2.1  High-Level Architecture Diagram", styles))
    story.append(sp(6))
    story.append(arch_diagram(styles))
    story.append(sp(8))
    story.append(Paragraph(
        "Figure 1 – CDSS High-Level Architecture: User → React Frontend → FastAPI Backend → "
        "AI Cascade (OpenRouter → Ollama → Rule Engine) → SQLite Database",
        styles["caption"]))
    story.append(sp(10))

    # 2.2
    story.append(sub_header("2.2  Component Interaction Flow", styles))
    flow_data = [
        ["Step", "Actor", "Action", "Protocol"],
        ["1", "Clinician",          "Opens browser, navigates to /consultation",        "—"],
        ["2", "Frontend",           "Renders Consultation form (React)",                "—"],
        ["3", "Clinician",          "Enters patient details, symptoms, vitals, notes",  "UI Interaction"],
        ["4", "Frontend → Backend", "POST /extract  with free-text clinical note",      "HTTP/JSON"],
        ["5", "Backend",            "Calls NLP extraction (LLM or regex fallback)",     "Internal"],
        ["6", "Backend → Frontend", "Returns ExtractedData (symptoms, vitals, age…)",   "HTTP/JSON"],
        ["7", "Frontend",           "Auto-fills form fields from extracted data",        "React State"],
        ["8", "Frontend → Backend", "POST /predict with full patient payload",           "HTTP/JSON"],
        ["9", "Backend → AI",       "Calls OpenRouter API with structured prompt",      "HTTPS/JSON"],
        ["10","AI → Backend",       "Returns JSON array of differential diagnoses",      "HTTPS/JSON"],
        ["11","Backend",            "Detects red flags, retrieves NHM treatments",       "Internal"],
        ["12","Backend → Frontend", "Returns complete DiagnosticResult object",          "HTTP/JSON"],
        ["13","Frontend",           "Stores result in sessionStorage, navigates to /diagnostic-results", "—"],
        ["14","Clinician",          "Reviews results, clicks 'Save Diagnostic to History'", "UI Click"],
        ["15","Frontend → Backend", "POST /patient/save  to persist in SQLite",          "HTTP/JSON"],
        ["16","Frontend",           "Also mirrors record to localStorage",               "Browser API"],
    ]
    story.append(colored_table(flow_data,
        [1.2*cm, 3.5*cm, 7.8*cm, 3.0*cm], header_bg=BLUE))
    story.append(PageBreak())

    # ── 3. FRONTEND ─────────────────────────────────────────────────────────
    story += section_header("3.  Frontend", styles)
    story.append(body(
        "The frontend is a <b>Single Page Application (SPA)</b> built with <b>React 19 + TypeScript</b> "
        "and bundled with <b>Vite 8</b>. It runs on <b>http://localhost:5173</b> during development. "
        "All pages are rendered client-side; routing is handled by React Router DOM v7 "
        "using nested routes under a shared Layout component.", styles))
    story.append(sp())

    # 3.1
    story.append(sub_header("3.1  Tech Stack & Configuration", styles))
    conf_data = [
        ["Item", "Value"],
        ["Entry Point",     "frontend/index.html  →  src/main.tsx  →  src/App.tsx"],
        ["Dev Server Port", "5173 (Vite default)"],
        ["Backend URL Env", "VITE_BACKEND_URL=http://localhost:8000  (frontend/.env)"],
        ["Font Imports",    "Plus Jakarta Sans + Inter  (Google Fonts CDN)"],
        ["CSS Strategy",    "Vanilla CSS with design tokens (CSS custom properties in index.css)"],
        ["Type Checking",   "TypeScript ~6.0 with strict tsconfig"],
        ["Linting",         "ESLint 10 with react-hooks + react-refresh plugins"],
    ]
    story.append(colored_table(conf_data, [5.0*cm, 11.0*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 3.2
    story.append(sub_header("3.2  Page Breakdown", styles))

    pages = [
        ("Layout.tsx  (components/)", EMERALD,
         "Persistent shell around every page. Renders: (a) full-screen video background on Home, dark mesh gradient on inner pages, (b) liquid-glass navigation pill with links to Home / AI Diagnostic / Patient History, (c) account icon linking to Dashboard, (d) hamburger mobile menu with backdrop-blur overlay, (e) <Outlet/> for child routes. Uses useLocation() to detect the home page and conditionally render the background video vs. the ambient gradient."),
        ("Home.tsx  (pages/)", BLUE,
         "Landing page with hero headline 'Refining Wellness Through Natural & Precision Care', a CTA button linking to /consultation, and a bottom statistics bar showing a practitioner count and a live engine status pulse indicator. Pure presentational—no backend calls."),
        ("Consultation.tsx  (pages/)", PURPLE,
         "The core AI diagnostic form (652 lines). Sections: (1) Free-Text Clinical Note textarea with an 'Extract with AI' button that calls POST /extract; (2) Patient Demographics (Name, Age, Sex); (3) Symptom Checkboxes (18 pre-defined symptoms from NHM list); (4) Vitals panel (Temperature, BP, Pulse, SpO2, RR); (5) Lab Values (Hb, WBC, Platelets, RBS); (6) Additional Notes. On submit, calls POST /predict. If backend is unreachable, a client-side buildMockResult() function provides a local offline fallback. Result is written to sessionStorage and user is navigated to /diagnostic-results."),
        ("DiagnosticResults.tsx  (pages/)", AMBER,
         "Displays the full AI diagnostic result from sessionStorage. Sections: Red Flag Alerts (red glass cards), Primary Diagnosis Spotlight with confidence bar, Differential Diagnosis Chart (Recharts horizontal BarChart), Differential Diagnoses list with NHM codes, NHM Treatment Guidelines list. Has a 'Save Diagnostic to History' button that calls POST /patient/save AND also writes to localStorage for instant UI update. Navigates to /history after saving."),
        ("Results.tsx  (pages/)", CYAN,
         "A read-only version of DiagnosticResults, used when a clinician clicks a row in Patient History. Loads the same sessionStorage payload but does NOT have the save-to-database button. The 'Back' button returns to /history."),
        ("PatientHistory.tsx  (pages/)", colors.HexColor("#0891b2"),
         "Patient records list fetched from GET /patient/history, merged with any additional records in localStorage (saved_patients key). Features: search by name or ID, filter by status (all / critical / moderate / stable), stat cards for total / critical / moderate counts, a tabular list with patient identity, last visit date, visit count, last diagnosis, and colour-coded status badge. Clicking a row stores the patient data in sessionStorage and navigates to /results."),
        ("Dashboard.tsx  (pages/)", colors.HexColor("#7c3aed"),
         "Analytics dashboard at /dashboard (linked from the account icon). Shows 4 metric cards (Today's Consultations, Red Flag Alerts, Avg. AI Accuracy 91.3%, Patients Registered) sourced from GET /patient/history + localStorage. A Recharts AreaChart displays static weekly consultation / alert data. Two CTA buttons: Start AI Diagnostic and View Patient History."),
    ]

    for name, color, desc in pages:
        s = ParagraphStyle("page_title",
            fontName="Helvetica-Bold", fontSize=10.5, textColor=WHITE,
            backColor=color, borderPad=7, spaceBefore=8, spaceAfter=4,
            leading=16
        )
        story.append(Paragraph(f"  📄  {name}", s))
        story.append(body(desc, styles))
        story.append(sp(4))
    story.append(sp())

    # 3.3
    story.append(sub_header("3.3  Design System & Styling", styles))
    story.append(body(
        "The visual language is defined entirely in <b>frontend/src/index.css</b>. "
        "There is no Tailwind or third-party CSS framework—utility classes used in JSX "
        "(e.g. <i>liquid-glass</i>, <i>liquid-input</i>) are hand-crafted in this stylesheet.", styles))
    design_data = [
        ["Token / Class",    "Value / Purpose"],
        ["--bg-primary",     "#050d1a  — Deep navy page background"],
        ["--accent-blue",    "#3b82f6  — Primary interactive blue"],
        ["--accent-emerald", "#10b981  — Success / stable status"],
        ["--accent-amber",   "#f59e0b  — Warning / moderate status"],
        ["--accent-red",     "#ef4444  — Error / critical / red flag"],
        [".liquid-glass",    "backdrop-filter: blur(12px)  +  rgba(255,255,255,0.06) bg  +  white border — glassmorphism effect on all cards, nav pills, and buttons"],
        [".liquid-input",    "Glass-styled text input — same blur + border treatment as cards"],
        [".bg-mesh",         "CSS radial-gradient ambient mesh used as background on inner pages"],
        ["Font stack",       "Plus Jakarta Sans → Inter → system-ui  (both imported from Google Fonts)"],
        ["Animation",        "CSS keyframe animations for pulse dots, spin loaders, and hover transitions"],
    ]
    story.append(colored_table(design_data, [4.5*cm, 11.5*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 3.4
    story.append(sub_header("3.4  State Management & Data Flow", styles))
    for b in [
        "<b>Local component state (useState):</b> form fields, loading flags, extraction results, filter values.",
        "<b>sessionStorage:</b> The key <i>cdss_result</i> is used to pass the full diagnostic result from Consultation → DiagnosticResults → Results pages without prop drilling or a global store.",
        "<b>localStorage:</b> The key <i>saved_patients</i> acts as a client-side cache that ensures Patient History and Dashboard show records even when the backend is temporarily unreachable.",
        "<b>No Redux / Zustand:</b> The app intentionally avoids a global state manager; navigation + storage APIs are sufficient given the current page count.",
        "<b>Data fetching:</b> All API calls use the native <i>fetch()</i> API with async/await. The BACKEND base URL is sourced from <i>import.meta.env.VITE_BACKEND_URL</i>.",
    ]:
        story.append(bullet_item(b, styles))
    story.append(PageBreak())

    # ── 4. BACKEND ──────────────────────────────────────────────────────────
    story += section_header("4.  Backend", styles)
    story.append(body(
        "The backend is a single-file <b>FastAPI</b> application (<b>backend/main.py</b>, 911 lines). "
        "It is served by <b>Uvicorn</b> on <b>http://0.0.0.0:8000</b> with hot-reload enabled in "
        "development. All heavy AI logic, NLP extraction, red-flag detection, and database "
        "persistence are handled here.", styles))
    story.append(sp())

    # 4.1
    story.append(sub_header("4.1  FastAPI Server", styles))
    server_data = [
        ["Attribute", "Value"],
        ["Entry point",       "backend/main.py"],
        ["App title",         "CDSS API"],
        ["Version",           "1.0.0"],
        ["Run command",       "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"],
        ["CORS policy",       "allow_origins=['*'], allow_methods=['*'], allow_headers=['*']"],
        ["Dependency injection", "SQLAlchemy Session via FastAPI Depends(get_db)"],
        ["Startup action",    "Base.metadata.create_all(bind=engine) — auto-creates tables"],
        ["Environment vars",  "Loaded from backend/.env via python-dotenv at startup"],
    ]
    story.append(colored_table(server_data, [5.0*cm, 11.0*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 4.2
    story.append(sub_header("4.2  API Endpoints", styles))
    endpoint_data = [
        ["Method", "Path",              "Purpose",                           "Auth"],
        ["GET",    "/",                 "Health check — returns version",    "None"],
        ["POST",   "/extract",          "NLP extraction from free text",     "None"],
        ["POST",   "/predict",          "Differential diagnosis + red flags + treatments", "None"],
        ["POST",   "/patient/save",     "Insert or update patient record",   "None"],
        ["GET",    "/patient/history",  "Retrieve all patient records (newest first)", "None"],
        ["DELETE", "/patient/history",  "Clear all patient records",         "None"],
    ]
    story.append(colored_table(endpoint_data,
        [1.8*cm, 4.0*cm, 8.0*cm, 2.2*cm], header_bg=BLUE))
    story.append(sp(10))

    # 4.3
    story.append(sub_header("4.3  Request / Response Schemas (Pydantic)", styles))
    schema_data = [
        ["Schema",            "Direction",  "Key Fields"],
        ["ExtractionRequest", "Request",    "text: str"],
        ["ExtractedData",     "Response",   "age, sex, symptoms[], vitals{}, duration, chiefComplaint, confidence, rawEntities[]"],
        ["PredictRequest",    "Request",    "name, freeText, age, sex, temperature, bp, pulse, spo2, rr, symptoms[], hb, wbc, platelets, rbs, notes, extractedData"],
        ["PredictResponse",   "Response",   "patient{id,name,age,sex}, symptoms[], vitals{}, labs{}, redFlags[], diagnoses[], treatments[], primaryDiagnosis, extractedData, timestamp"],
        ["SavePatientRequest","Request",    "id, name, age, sex, condition, status"],
        ["SavePatientResponse","Response",  "status, message, patient{id,name,age,sex,condition,status,lastVisit}"],
    ]
    story.append(colored_table(schema_data,
        [4.5*cm, 2.5*cm, 9.0*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 4.4
    story.append(sub_header("4.4  Middleware & CORS", styles))
    story.append(info_box(
        "<b>CORSMiddleware</b> is configured with <i>allow_origins=['*']</i> for development. "
        "This permits the React dev server (port 5173) to communicate with the FastAPI server (port 8000) "
        "without browser CORS errors. In production, this should be tightened to the specific "
        "frontend domain. No authentication middleware is currently configured — this is a "
        "known limitation (see Section 11).", styles))
    story.append(PageBreak())

    # ── 5. AI & ML ENGINE ────────────────────────────────────────────────────
    story += section_header("5.  AI & Machine Learning Engine", styles)
    story.append(body(
        "The AI engine is a three-tier cascade. The system always attempts the highest-quality "
        "model first and gracefully degrades to ensure a response is always returned, even in "
        "fully offline environments.", styles))
    story.append(sp())

    # 5.1
    story.append(sub_header("5.1  AI Pipeline Overview", styles))
    pipeline_data = [
        ["Tier", "Provider",          "Model",                            "Trigger Condition"],
        ["1 (Primary)",  "OpenRouter API", "google/gemma-4-26b-a4b-it:free",  "Always attempted first"],
        ["1 (Fallback)", "OpenRouter API", "nvidia/nemotron-3-nano-30b-a3b",  "If primary returns HTTP error"],
        ["1 (Fallback)", "OpenRouter API", "google/gemma-4-31b-it:free",      "If previous model fails"],
        ["1 (Fallback)", "OpenRouter API", "nvidia/nemotron-3-ultra-550b",    "Tertiary OpenRouter fallback"],
        ["2",  "Ollama (local)", "gemma2:2b  @ localhost:11434",    "If OpenRouter entirely fails"],
        ["3",  "Rule Engine",   "Pure Python, no external calls",   "If Ollama unavailable / timeout"],
    ]
    story.append(colored_table(pipeline_data,
        [2.5*cm, 3.5*cm, 6.0*cm, 4.0*cm], header_bg=PURPLE))
    story.append(sp())

    # 5.2
    story.append(sub_header("5.2  OpenRouter API (Primary)", styles))
    story.append(body(
        "OpenRouter is an API aggregator that provides unified access to dozens of free and "
        "paid LLMs. The CDSS uses it as the primary AI provider because it offers large-context "
        "models (26B+ parameters) for free, significantly outperforming the local 2B model.", styles))
    for b in [
        "<b>Endpoint:</b>  https://openrouter.ai/api/v1/chat/completions",
        "<b>Auth:</b>  Bearer token in Authorization header (OPENROUTER_API_KEY from .env)",
        "<b>Temperature:</b>  0.2 — low temperature for deterministic clinical output",
        "<b>System prompt:</b>  'You are a clinical decision support system AI. Respond concisely with exact data.'",
        "<b>Thinking models:</b>  payload includes <i>thinking: {type: disabled}</i> to suppress chain-of-thought XML that would break JSON parsing",
        "<b>Timeout:</b>  20 seconds per request",
        "<b>Retry logic:</b>  Iterates through all models in OPENROUTER_FALLBACKS list on failure",
    ]:
        story.append(bullet_item(b, styles))
    story.append(sp())

    # 5.3
    story.append(sub_header("5.3  Local Ollama / Gemma2 2B (Secondary Fallback)", styles))
    story.append(body(
        "If all OpenRouter calls fail, the system falls back to a locally-running Ollama server. "
        "This enables completely offline operation in areas with unreliable internet — critical for "
        "rural Indian healthcare settings.", styles))
    for b in [
        "<b>Endpoint:</b>  http://localhost:11434/api/generate",
        "<b>Model:</b>  gemma2:2b  (OLLAMA_MODEL env variable, default: gemma2:2b)",
        "<b>Stream:</b>  False — single synchronous response",
        "<b>Timeout:</b>  60 seconds (longer due to local CPU/GPU inference latency)",
        "<b>num_predict:</b>  1024 tokens max",
        "<b>Temperature:</b>  0.2",
        "<b>Error handling:</b>  ConnectionError (Ollama not running), Timeout, generic exceptions all caught and logged",
    ]:
        story.append(bullet_item(b, styles))
    story.append(sp())

    # 5.4
    story.append(sub_header("5.4  Rule-Based Engine (Offline Hard Fallback)", styles))
    story.append(body(
        "A deterministic scoring engine that requires no external services. It matches symptoms "
        "and free text against a knowledge base of 11 diseases using keyword matching + "
        "weighted scoring.", styles))
    story.append(sp(4))
    story.append(body("<b>Disease Knowledge Base (11 conditions):</b>", styles))
    disease_data = [
        ["Disease", "Required Keywords", "Supportive Keywords", "Base Score"],
        ["Bacterial Meningitis",         "fever, neck stiff",   "headache, sensorium, vomit, rash", "0.82"],
        ["Malaria (P. falciparum)",      "fever, chill",        "headache, fatigue, vomit, joint",  "0.79"],
        ["Dengue Fever",                 "fever",               "rash, joint, headache, fatigue",   "0.72"],
        ["Typhoid Fever",                "fever",               "headache, abdominal, diarrh",      "0.68"],
        ["Acute Gastroenteritis",        "diarrh, vomit",       "fever, abdominal, fatigue",        "0.74"],
        ["Acute Coronary Syndrome",      "chest",               "breath, fatigue, sweat",           "0.77"],
        ["Viral Hepatitis A",            "jaundice",            "abdominal, fatigue, fever",        "0.71"],
        ["Leptospirosis",                "fever, joint",        "jaundice, headache, muscle",       "0.64"],
        ["URTI",                         "cough",               "fever, throat, ear, fatigue",      "0.67"],
        ["Acute Viral Fever",            "fever",               "fatigue, headache, chill",         "0.60"],
        ["Urinary Tract Infection",      "fever",               "fatigue, abdominal, dysuria",      "0.55"],
    ]
    story.append(colored_table(disease_data,
        [4.5*cm, 4.0*cm, 4.5*cm, 2.0*cm], header_bg=DARK_BLUE))
    story.append(sp(6))
    story.append(body(
        "<b>Scoring algorithm:</b> base_score + (supportive_matches × 0.04) + text_direct_match_bonus (0.15) "
        "+ lab_bonus (0.08–0.10 for abnormal platelets/WBC). Scores capped at 0.98.", styles))
    story.append(sp())

    # 5.5
    story.append(sub_header("5.5  NLP Extraction Logic", styles))
    story.append(body(
        "The <b>/extract</b> endpoint converts free-text clinical notes into structured fields. "
        "Three implementations are stacked (LLM primary, then regex fallback):", styles))
    for b in [
        "<b>LLM Extraction (OpenRouter/Ollama):</b> Sends structured prompt asking for JSON output with age, sex, symptoms[], vitals{}, duration, chiefComplaint, confidence, rawEntities[].",
        "<b>Regex Fallback:</b> Uses hand-crafted regex patterns for age (\\d{1,3}\\s*year), sex (male|female|M|F), duration (\\d+ day/week/hour/month), temperature (temp:\\s+\\d{2,3}), BP (bp:\\s+\\d{2,3}/\\d{2,3}), pulse, SpO2.",
        "<b>Symptom Pattern Dictionary:</b> 18 symptom categories each with multiple keyword patterns (e.g. 'Fever' matches: fever, febrile, pyrexia, temperature, high temp).",
        "<b>Confidence scoring:</b> 0.5 + (0.08 × symptom_count) + 0.1 if age found + 0.05 if sex found, capped at 0.95.",
    ]:
        story.append(bullet_item(b, styles))
    story.append(sp())

    # 5.6
    story.append(sub_header("5.6  Prompt Engineering", styles))
    story.append(body(
        "Both prompts are carefully engineered for reliable structured output from small LLMs:", styles))
    story.append(code_block(
        'DIAGNOSE PROMPT (excerpt):\n'
        '"OUTPUT RULE: Reply with ONLY the raw JSON array below. No words before it,\n'
        ' no words after it, no markdown fences.\n'
        ' Patient: Free-Text: {free_text} | Symptoms: {symptoms} | Vitals: {vitals}\n'
        ' Required: [{\"name\": \"Disease\", \"confidence\": 0.85, \"shap\": [\"finding1\"]}]\n'
        ' Start reply with \'[\' and end with \']\'. Nothing else."', styles))
    story.append(code_block(
        'EXTRACT PROMPT (excerpt):\n'
        '"OUTPUT RULE: Reply with ONLY the raw JSON object below.\n'
        ' Clinical Note: \"\"\"{text}\"\"\"\n'
        ' Required: {\"age\": \"45 years\", \"sex\": \"male\", \"symptoms\": [...],\n'
        '           \"vitals\": {\"temperature\":\"\", \"bp\":\"\", ...},\n'
        '           \"chiefComplaint\": \"...\", \"confidence\": 0.9, \"rawEntities\": [...]}\n'
        ' Start reply with \'{\' and end with \'}\'. Nothing else."', styles))
    story.append(sp())

    # 5.7
    story.append(sub_header("5.7  JSON Extraction Utilities", styles))
    for b in [
        "<b>strip_thinking_tags():</b> Removes &lt;think&gt;...&lt;/think&gt; chain-of-thought blocks emitted by reasoning models (Qwen3, DeepSeek-R1) before JSON parsing.",
        "<b>extract_json_array():</b> Robustly finds the first '[' in LLM output, counts bracket depth to find the matching ']', and calls json.loads(). Strips markdown fences first.",
        "<b>extract_json_object():</b> Same algorithm for JSON objects ('{' → '}' matching).",
    ]:
        story.append(bullet_item(b, styles))
    story.append(PageBreak())

    # ── 6. DATABASE ──────────────────────────────────────────────────────────
    story += section_header("6.  Database", styles)

    # 6.1
    story.append(sub_header("6.1  Database Engine & ORM", styles))
    story.append(body(
        "The database layer uses <b>SQLAlchemy 2.x ORM</b> configured in <b>backend/database.py</b>. "
        "SQLite is the default; PostgreSQL can be activated by setting DATABASE_URL in the .env file.", styles))
    db_data = [
        ["Config Item",    "Value"],
        ["Default DB",     "SQLite — file: backend/cdss.db"],
        ["Optional DB",    "PostgreSQL — e.g. postgresql://postgres:pass@localhost:5432/cdss"],
        ["ORM",            "SQLAlchemy 2.x  (declarative_base style)"],
        ["Session factory","SessionLocal = sessionmaker(autocommit=False, autoflush=False)"],
        ["SQLite flag",    "check_same_thread=False — allows FastAPI thread pool to reuse sessions"],
        ["Connection",     "DATABASE_URL env var; auto-detects SQLite vs. PostgreSQL by prefix"],
        ["Table creation", "Base.metadata.create_all(bind=engine) runs at app startup"],
    ]
    story.append(colored_table(db_data, [4.5*cm, 11.5*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 6.2
    story.append(sub_header("6.2  Schema & Models (backend/models.py)", styles))
    schema_table = [
        ["Column",     "SQLAlchemy Type", "Constraints",         "Description"],
        ["id",         "String",          "PK, index",           "Patient ID, format P-XXXXXXXX (UUID)"],
        ["name",       "String",          "index",               "Patient full name"],
        ["age",        "String",          "—",                   "Age as string (e.g. '45')"],
        ["sex",        "String",          "—",                   "'male' or 'female'"],
        ["condition",  "String",          "—",                   "Primary diagnosis (AI result)"],
        ["status",     "String",          "—",                   "'stable', 'moderate', or 'critical'"],
        ["time",       "String",          "—",                   "Human-readable time string 'Just now'"],
        ["timestamp",  "DateTime",        "default=utcnow",      "Auto-set to current UTC time on insert"],
    ]
    story.append(colored_table(schema_table,
        [2.5*cm, 2.8*cm, 3.0*cm, 7.7*cm], header_bg=DARK_BLUE))
    story.append(sp())

    # 6.3
    story.append(sub_header("6.3  CRUD Operations", styles))
    crud_data = [
        ["Operation", "Endpoint",           "Logic"],
        ["Read All",  "GET /patient/history",  "Query Consultation ordered by timestamp DESC, map to JSON"],
        ["Upsert",    "POST /patient/save",    "Filter by id; if exists → update fields, else → insert new record"],
        ["Delete All","DELETE /patient/history","db.query(Consultation).delete(); commit"],
    ]
    story.append(colored_table(crud_data,
        [2.8*cm, 4.5*cm, 8.7*cm], header_bg=BLUE))
    story.append(sp())

    # 6.4
    story.append(sub_header("6.4  Client-Side Fallback Storage (localStorage)", styles))
    story.append(info_box(
        "Key: <b>saved_patients</b>  (JSON array in browser localStorage)<br/><br/>"
        "The frontend always writes a copy of each saved patient to localStorage immediately "
        "after calling POST /patient/save (even if the backend call fails). "
        "On page load, PatientHistory.tsx and Dashboard.tsx fetch from the backend first, "
        "then merge any additional records from localStorage that are not already present "
        "(de-duplicated by patient id). This dual-write strategy ensures the UI remains "
        "responsive and fully functional even when the backend server is temporarily unreachable.", styles))
    story.append(PageBreak())

    # ── 7. RED FLAG DETECTION ────────────────────────────────────────────────
    story += section_header("7.  Red Flag Detection Engine", styles)
    story.append(body(
        "The <b>detect_red_flags()</b> function in main.py is called on every /predict request "
        "BEFORE the LLM diagnosis to instantly surface life-threatening conditions. "
        "It is pure Python — no AI required — ensuring zero latency alerting.", styles))
    story.append(sp())
    rf_data = [
        ["Red Flag Rule",      "Trigger Condition",               "Alert Message"],
        ["Meningitis Risk",    "fever + neck stiff in symptoms",  "High Fever + Neck Stiffness → Immediate LP & IV Antibiotics"],
        ["Cardiac Emergency",  "chest + breath in symptoms",      "Chest Pain + Breathlessness → ECG immediately. Call 108"],
        ["Neuro Emergency",    "sensorium / altered in symptoms", "Altered Sensorium → Rule out meningitis/stroke/hypoglycaemia"],
        ["Shock (Hypotension)","Systolic BP < 90 mmHg",           "Hypotension (BP {value}) → IV Fluids. Urgent referral"],
        ["Hypoxia",            "SpO₂ < 92%",                     "SpO₂ {value}% → High-flow oxygen immediately"],
        ["Hyperpyrexia",       "Temperature ≥ 40.0°C",           "Hyperpyrexia ({value}°C) → Risk of febrile seizures"],
        ["Tachycardia",        "Pulse > 120 bpm",                 "Tachycardia ({value} bpm) → Rule out sepsis/arrhythmia"],
    ]
    story.append(colored_table(rf_data,
        [4.0*cm, 4.5*cm, 7.5*cm], header_bg=RED))
    story.append(sp(8))
    story.append(info_box(
        "⚠️  <b>Important:</b> Red flags are detected server-side and returned in the "
        "<i>redFlags[]</i> array of the /predict response. The frontend renders them as "
        "prominent red glass alert cards at the top of the DiagnosticResults page. "
        "If any red flag is present, the 'Recommended Action' panel automatically shows "
        "'Urgent Hospital Referral' instead of 'Outpatient Treatment'.", styles,
        bg=colors.HexColor("#fef2f2"), border=RED))
    story.append(PageBreak())

    # ── 8. NHM TREATMENT PROTOCOL ────────────────────────────────────────────
    story += section_header("8.  NHM Treatment Protocol (Knowledge Base / RAG)", styles)
    story.append(body(
        "After diagnosis, the backend performs a <b>Retrieval-Augmented Generation (RAG)</b> "
        "step — it looks up the primary diagnosis in the <b>NHM_TREATMENTS</b> dictionary "
        "and returns evidence-based drug, dosage, duration, and referral guidance. "
        "This is a curated static knowledge base, not a vector database, ensuring "
        "100% reliability without an external embedding service.", styles))
    story.append(sp())
    nhm_data = [
        ["Disease",                    "Drug 1",                "Drug 2"],
        ["Malaria (P. falciparum)",     "Artemether-Lumefantrine 4 tabs BD × 3 days", "Primaquine 0.75 mg/kg single dose"],
        ["Malaria (P. vivax)",          "Chloroquine 10 mg/kg × 3 days",              "Primaquine 0.25 mg/kg × 14 days"],
        ["Dengue Fever",               "Paracetamol 500-1000mg q6h",                 "ORS / IV Fluids (maintain hydration)"],
        ["Typhoid Fever",              "Azithromycin 500mg OD × 7 days",             "Ceftriaxone IV 2g OD × 10-14 days"],
        ["Acute Gastroenteritis",      "ORS 200-400 mL per stool",                   "Zinc 20mg OD × 14 days (child <5yr)"],
        ["Bacterial Meningitis",       "Ceftriaxone IV 2g q12h × 10-14 days",        "Dexamethasone IV 0.15 mg/kg q6h × 4 days"],
        ["Acute Coronary Syndrome",    "Aspirin 325mg stat (chew)",                  "Clopidogrel 300mg loading dose stat"],
        ["Hypertension",               "Amlodipine 5-10mg OD",                       "Losartan 50mg OD"],
        ["Viral Hepatitis A",          "Supportive care + high-carb diet",           "Vitamin K 10mg IM × 3 days"],
        ["Leptospirosis",              "Doxycycline 100mg BD × 7 days",              "Penicillin G IV 1.5 MU q6h × 7 days"],
        ["URTI",                       "Paracetamol 500-1000mg q6-8h PRN",           "Saline Nasal Drops × 5 days"],
        ["Acute Viral Fever",          "Paracetamol 500-1000mg q6-8h",               "ORS as needed for hydration"],
    ]
    story.append(colored_table(nhm_data,
        [4.5*cm, 6.0*cm, 5.5*cm], header_bg=EMERALD))
    story.append(sp(6))
    story.append(body(
        "If the primary diagnosis does not match any key in NHM_TREATMENTS, "
        "a <b>DEFAULT_TREATMENT</b> response is returned: Paracetamol 500-1000mg q6-8h "
        "+ ORS with a follow-up-in-48h referral note.", styles))
    story.append(PageBreak())

    # ── 9. END-TO-END WORKFLOW ───────────────────────────────────────────────
    story += section_header("9.  End-to-End Workflow", styles)

    # 9.1
    story.append(sub_header("9.1  Consultation Workflow (Main Diagnostic Path)", styles))
    story.append(sp(4))
    wf1 = [
        ["#", "Step",              "Details"],
        ["1",  "Open App",         "Doctor navigates to http://localhost:5173"],
        ["2",  "Navigate",         "Clicks 'Start AI Diagnostic' → /consultation"],
        ["3",  "Enter Note",       "Types or pastes free-text clinical note in textarea"],
        ["4",  "Extract (optional)","Clicks 'Extract with AI' → POST /extract → fields auto-filled"],
        ["5",  "Fill Form",        "Optionally adds/edits symptoms, vitals, lab values, name"],
        ["6",  "Submit",           "Clicks 'Start AI Diagnostic' button"],
        ["7",  "POST /predict",    "Frontend sends full PredictRequest payload to backend"],
        ["8",  "NLP on freeText",  "Backend calls extract_nlp(freeText) to supplement symptoms"],
        ["9",  "Red Flag Check",   "detect_red_flags(symptoms, vitals) → flags[]"],
        ["10", "AI Diagnosis",     "predict_diagnoses() → OpenRouter → Ollama → Rule Engine"],
        ["11", "Treatment Lookup", "NHM_TREATMENTS.get(primaryDiagnosis)"],
        ["12", "Response",         "Backend returns JSON: patient, diagnoses, redFlags, treatments"],
        ["13", "Navigate",         "Frontend writes to sessionStorage → navigates to /diagnostic-results"],
        ["14", "Display",          "DiagnosticResults.tsx renders: alerts, primary dx, chart, treatments"],
    ]
    story.append(colored_table(wf1, [1.0*cm, 3.5*cm, 11.5*cm], header_bg=BLUE))
    story.append(sp(10))

    # 9.2
    story.append(sub_header("9.2  Data Save Workflow", styles))
    wf2 = [
        ["#", "Step",           "Details"],
        ["1",  "View Results",  "Doctor reviews DiagnosticResults page"],
        ["2",  "Click Save",    "Clicks 'Save Diagnostic to History' button"],
        ["3",  "POST /patient/save", "Frontend sends {id, name, age, sex, condition, status} to backend"],
        ["4",  "DB Upsert",     "Backend checks if id exists → update or insert in SQLite"],
        ["5",  "localStorage",  "Frontend ALSO writes record to localStorage['saved_patients'] immediately"],
        ["6",  "UI Update",     "Button turns green: 'Saved to History Database'"],
        ["7",  "Navigate",      "Optionally click 'View History Archive →' to go to /history"],
    ]
    story.append(colored_table(wf2, [1.0*cm, 3.5*cm, 11.5*cm], header_bg=EMERALD))
    story.append(sp(10))

    # 9.3
    story.append(sub_header("9.3  Patient History Workflow", styles))
    wf3 = [
        ["#", "Step",            "Details"],
        ["1",  "Navigate",       "Click 'Patient History' in navbar → /history"],
        ["2",  "Fetch Backend",  "GET /patient/history → SQLAlchemy query → JSON list"],
        ["3",  "Merge Local",    "Frontend merges localStorage['saved_patients'] for records not in DB"],
        ["4",  "Display List",   "Renders patient rows with status badges, diagnoses, last visit"],
        ["5",  "Search",         "Filter by name or patient ID (case-insensitive)"],
        ["6",  "Filter Badge",   "Click 'critical' / 'moderate' / 'stable' to filter by status"],
        ["7",  "Click Row",      "Writes summary to sessionStorage, navigates to /results"],
        ["8",  "View Results",   "Results.tsx shows the historical diagnostic record (read-only)"],
    ]
    story.append(colored_table(wf3, [1.0*cm, 3.5*cm, 11.5*cm], header_bg=CYAN))
    story.append(PageBreak())

    # ── 10. ENVIRONMENT ──────────────────────────────────────────────────────
    story += section_header("10.  Environment & Configuration", styles)
    env_data = [
        ["File",                  "Variable",             "Default / Example",               "Purpose"],
        ["backend/.env",          "OPENROUTER_API_KEY",   "sk-or-v1-…",                      "Auth token for OpenRouter REST API"],
        ["backend/.env",          "OPENROUTER_MODEL",     "google/gemma-4-26b-a4b-it:free",  "Primary LLM model to use"],
        ["backend/.env",          "DATABASE_URL",         "sqlite:///./cdss.db",             "DB connection string (omit for SQLite default)"],
        ["backend/.env",          "OLLAMA_URL",           "http://localhost:11434",           "Ollama server base URL"],
        ["backend/.env",          "OLLAMA_MODEL",         "gemma2:2b",                       "Local Ollama model name"],
        ["frontend/.env",         "VITE_BACKEND_URL",     "http://localhost:8000",           "Backend URL used by React app"],
        ["frontend/.env",         "VITE_OPENROUTER_API_KEY","sk-or-v1-…",                   "Stored in frontend (not currently used in production code)"],
    ]
    story.append(colored_table(env_data,
        [3.5*cm, 4.5*cm, 4.5*cm, 3.5*cm], header_bg=DARK_BLUE))
    story.append(sp())
    story.append(info_box(
        "📁 <b>Files Structure:</b><br/>"
        "CDSS/<br/>"
        "&nbsp;&nbsp;├── backend/<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── main.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# FastAPI app + AI logic + routes (911 lines)<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── database.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# SQLAlchemy engine + session factory<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── models.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# Consultation ORM model<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── requirements.txt&nbsp;"
        "# Python dependencies<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── cdss.db&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# SQLite database file (auto-created)<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── .env&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# OpenRouter API key + model config<br/>"
        "&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── test_gemma.py&nbsp;&nbsp;&nbsp;"
        "# Dev script to test Ollama connection<br/>"
        "&nbsp;&nbsp;└── frontend/<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── src/<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── App.tsx&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# React Router config (6 routes)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── index.css&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# Full design system (344 lines)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── main.tsx&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# React 19 createRoot entry<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── components/<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── Layout.tsx&nbsp;&nbsp;"
        "# Shared navigation + background shell<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── pages/ (6 pages)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── .env&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# VITE_BACKEND_URL<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── package.json&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "# React 19 + Vite 8 + Recharts + Lucide", styles))
    story.append(PageBreak())

    # ── 11. SECURITY ─────────────────────────────────────────────────────────
    story += section_header("11.  Security Considerations", styles)
    sec_data = [
        ["Area",               "Current State",                       "Recommended Improvement"],
        ["Authentication",     "None — all endpoints are public",     "Add JWT Bearer token auth (FastAPI-Users or custom)"],
        ["CORS",               "allow_origins=['*'] (wide open)",     "Restrict to specific frontend domain in production"],
        ["API Keys",           "Stored in .env files (not committed)", "Use a secrets manager (e.g. AWS Secrets Manager) in production"],
        ["Input Validation",   "Pydantic models validate field types", "Add length limits, field sanitization, SQL injection check"],
        ["HTTPS",              "HTTP only in development",            "Configure TLS/HTTPS via reverse proxy (nginx/Caddy) in production"],
        ["Rate Limiting",      "Not implemented",                     "Add slowapi middleware to prevent API abuse"],
        ["Patient Data",       "No encryption at rest (SQLite)",      "Use PostgreSQL with encrypted volumes in production"],
        ["Session Storage",    "Diagnostic results in sessionStorage","sessionStorage is cleared on tab close; acceptable for ephemeral data"],
    ]
    story.append(colored_table(sec_data,
        [3.5*cm, 5.0*cm, 7.5*cm], header_bg=RED))
    story.append(PageBreak())

    # ── 12. LIMITATIONS & ROADMAP ────────────────────────────────────────────
    story += section_header("12.  Known Limitations & Roadmap", styles)
    story.append(sub_header("Current Limitations", styles))
    limits = [
        "No authentication — any user with network access can call all endpoints.",
        "CORS is fully open (allow_origins=['*']) — not safe for production deployment.",
        "The Dashboard's weekly chart uses <b>static mock data</b>, not real time-series queries.",
        "Patient visit count is always hardcoded to 1 — no true visit tracking.",
        "No ML model training — the rule-based fallback is keyword-matching, not a trained classifier.",
        "The OPENROUTER_API_KEY in frontend/.env is currently unused — all AI calls go through backend.",
        "No audit trail — there is no logging of who accessed which patient record.",
        "SQLite is single-writer — concurrent writes from multiple staff may cause locking issues.",
    ]
    for l in limits:
        story.append(bullet_item(l, styles))
    story.append(sp())

    story.append(sub_header("Roadmap & Future Enhancements", styles))
    roadmap = [
        "<b>Phase 1:</b> Add JWT authentication, role-based access (admin / doctor / nurse).",
        "<b>Phase 1:</b> Switch CORS to production domain only; add rate limiting.",
        "<b>Phase 2:</b> Replace SQLite with PostgreSQL; add Alembic migrations.",
        "<b>Phase 2:</b> Implement real visit-count tracking; multi-visit patient timeline.",
        "<b>Phase 3:</b> Train an XGBoost or LightGBM classifier on labelled symptom-disease data to replace the rule-based fallback.",
        "<b>Phase 3:</b> Integrate a proper vector database (ChromaDB / Pinecone) for semantic RAG over a larger NHM guideline corpus.",
        "<b>Phase 4:</b> Add voice input for free-text notes (Web Speech API).",
        "<b>Phase 4:</b> Generate a printable PDF diagnostic report per patient consultation.",
        "<b>Phase 5:</b> Integrate with India's ABDM / ABHA health ID system for national patient record linkage.",
        "<b>Phase 5:</b> Multi-language support (Hindi, Tamil, Marathi) for rural clinics.",
    ]
    for r in roadmap:
        story.append(bullet_item(r, styles))
    story.append(sp(20))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    story.append(sp(8))
    story.append(Paragraph(
        "End of CDSS Project Technical Documentation  ·  Generated " +
        datetime.datetime.now().strftime("%d %B %Y, %H:%M"),
        ParagraphStyle("footer_note", fontName="Helvetica-Oblique", fontSize=8.5,
                       textColor=MID_GRAY, alignment=TA_CENTER)
    ))

    return story


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    styles = make_styles()
    story  = build_story(styles)

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 30,
        bottomMargin=MARGIN + 20,
        title="CDSS – Clinical Decision Support System Architecture",
        author="CDSS Development Team",
        subject="Full Technical Documentation",
    )

    # Define page templates
    frame = Frame(MARGIN, MARGIN + 20, PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN - 50,
                  id="main", showBoundary=0)
    cover_template  = PageTemplate(id="cover",  frames=[frame], onPage=cover_page_cb)
    normal_template = PageTemplate(id="normal", frames=[frame], onPage=header_footer)

    doc.addPageTemplates([cover_template, normal_template])

    doc.build(story)
    print(f"\nPDF generated successfully: {OUTPUT_FILE}")
    print(f"    Location: {__import__('os').path.abspath(OUTPUT_FILE)}\n")


if __name__ == "__main__":
    main()
