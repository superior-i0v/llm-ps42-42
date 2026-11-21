"""Helper functions for the Cover Letter Generator (PS 42)."""
import io
import os
import re

from docx import Document
from docx.shared import Pt
from pypdf import PdfReader

# Models tried in order; if one is retired by Groq (404), the next is used.
# You can force one by setting LLM_MODEL in .env
MODELS = [m for m in [os.getenv("LLM_MODEL"), "openai/gpt-oss-120b", "openai/gpt-oss-20b"] if m]

SYSTEM_PROMPT = (
    "You are an expert career coach who writes concise, professional cover letters. "
    "You use ONLY facts that appear in the candidate's resume. "
    "You never invent employers, degrees, skills, numbers, dates or achievements."
)

USER_PROMPT = """Write a cover letter of about {words} words.

RULES:
1. Use only the real details from the RESUME below. If something is not in the resume, do not mention it.
2. Match the candidate's strongest relevant skills and projects to the requirements in the JOB DESCRIPTION.
3. Structure: greeting, opening paragraph (role + company + interest), one or two body paragraphs
   (skills and projects that match the job), closing paragraph (call to action), sign-off.
4. Tone: {tone}.
5. Address it to "Hiring Manager" and mention the company name "{company}".
6. Output only the letter text. No notes, no markdown, no placeholders like [Your Name]
   (use the name from the resume).

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""


def extract_pdf_text(file) -> str:
    """Return all text from an uploaded PDF (file-like object)."""
    reader = PdfReader(file)
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def build_prompt(resume: str, jd: str, company: str, tone: str, words: int = 250) -> str:
    return USER_PROMPT.format(
        words=words, tone=tone, company=company, resume=resume.strip(), jd=jd.strip()
    )


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def unsupported_numbers(letter: str, resume: str) -> list[str]:
    """Numbers in the letter that never appear in the resume (possible hallucination)."""
    nums = set(re.findall(r"\d+(?:\.\d+)?", letter))
    resume_nums = set(re.findall(r"\d+(?:\.\d+)?", resume))
    return sorted(nums - resume_nums)


def generate_letter(client, resume: str, jd: str, company: str, tone: str, words: int = 250) -> str:
    """Call the LLM and return the cover letter text."""
    last_error = None
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_prompt(resume, jd, company, tone, words)},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:  # model retired / not available -> try the next one
            last_error = e
            if "model" not in str(e).lower():
                raise
    raise last_error


def letter_to_docx(letter: str) -> bytes:
    """Convert the letter text to .docx bytes for download."""
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    for para in letter.split("\n\n"):
        doc.add_paragraph(para.strip())
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def letter_to_pdf(letter: str) -> bytes:
    """Convert the letter text to a clean A4 PDF (bytes) for download."""
    from xml.sax.saxutils import escape

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    # Standard PDF fonts only cover Western characters: swap look-alikes, drop the rest
    for bad, good in {"\u202f": " ", "\u00a0": " ", "\u2011": "-", "\u2010": "-"}.items():
        letter = letter.replace(bad, good)
    letter = letter.encode("cp1252", "replace").decode("cp1252")

    style = ParagraphStyle("letter", fontName="Times-Roman", fontSize=12, leading=17)
    story = []
    for para in letter.split("\n\n"):
        if para.strip():
            story += [Paragraph(escape(para.strip()).replace("\n", "<br/>"), style), Spacer(1, 10)]
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                      topMargin=2.5 * cm, bottomMargin=2.5 * cm).build(story)
    return buf.getvalue()
