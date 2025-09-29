# pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib import enums
from PyPDF2 import PdfReader, PdfWriter

def generate_resume_pdf(filename, name, base_resume_text, new_bullets):
    """
    Creates a new PDF that contains the candidate name, the extracted resume text,
    and the new AI-suggested bullets. This PDF can be appended to the original resume.
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal = styles["Normal"]

    story.append(Paragraph(f"{name}", title_style))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("<b>Extracted Resume Content</b>", heading_style))
    # keep the resume text as a paragraph (could be long)
    for chunk in split_text_for_paragraphs(base_resume_text, 1000):
        story.append(Paragraph(chunk.replace("\n", "<br/>"), normal))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>AI Suggested Bullets</b>", heading_style))
    for b in new_bullets:
        story.append(Paragraph(f"• {b}", normal))
        story.append(Spacer(1, 0.15*cm))

    doc.build(story)


def generate_cover_letter_pdf(filename, company, cover_letter_text):
    """
    Creates a PDF for the personalized cover letter.
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = styles["Title"]
    normal = styles["Normal"]

    story.append(Paragraph(f"Cover Letter — {company}", title_style))
    story.append(Spacer(1, 0.4*cm))

    # cover_letter_text may contain newlines; render as paragraph
    for chunk in split_text_for_paragraphs(cover_letter_text, 1000):
        story.append(Paragraph(chunk.replace("\n", "<br/>"), normal))
        story.append(Spacer(1, 0.2*cm))

    doc.build(story)


def split_text_for_paragraphs(text, max_chars=1000):
    """
    Helper: split long text into list of chunks under max_chars, splitting on double newlines if possible.
    """
    if not text:
        return [""]
    parts = text.split("\n\n")
    chunks = []
    current = ""
    for p in parts:
        if len(current) + len(p) + 2 <= max_chars:
            current += (p + "\n\n")
        else:
            if current:
                chunks.append(current.strip())
            if len(p) <= max_chars:
                current = p + "\n\n"
            else:
                # if single portion too large, split by sentences (rough)
                sub = [p[i:i+max_chars] for i in range(0, len(p), max_chars)]
                for s in sub:
                    chunks.append(s.strip())
                current = ""
    if current:
        chunks.append(current.strip())
    return chunks


def merge_pdfs_as_single(input_paths, output_path):
    """
    Merge many PDFs into a single PDF (preserves order).
    input_paths: list of file paths
    """
    writer = PdfWriter()
    for p in input_paths:
        reader = PdfReader(p)
        for page in reader.pages:
            writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
