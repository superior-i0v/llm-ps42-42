"""PS 42 - Cover Letter Generator (Streamlit + Groq LLM)."""
import html
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from utils import (
    extract_pdf_text,
    generate_letter,
    letter_to_docx,
    letter_to_pdf,
    unsupported_numbers,
    word_count,
)

load_dotenv()
st.set_page_config(page_title="Cover Letter Generator", page_icon="✉️", layout="wide")

# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

html, body, [class*="css"], .stApp { font-family: 'DM Sans', system-ui, sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.6rem !important; max-width: 1250px; }
[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"], [data-testid="stDeployButton"] { display: none; }

/* header */
.app-header { display:flex; align-items:center; gap:16px; margin:0 0 1.4rem 0; }
.app-logo { width:58px; height:58px; border-radius:14px; background:#1F2A44; color:#fff;
            display:flex; align-items:center; justify-content:center; font-size:28px; flex-shrink:0; }
.app-title { font-family:'Lora', Georgia, serif !important; font-size:2.3rem !important; font-weight:600 !important;
             color:#1F2A44 !important; line-height:1.1 !important; margin:0 !important; }
.app-sub { font-size:1rem !important; color:#5B6785 !important; margin:6px 0 0 0 !important; }

/* cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background:#FFFFFF; border:1px solid #DCE2EC !important; border-radius:14px;
}
.section-title { font-weight:700; color:#1F2A44; font-size:1.05rem; margin:0 0 .3rem 0; }

/* inputs */
div[data-testid="stFileUploader"] section { border:1.5px dashed #AEB9D0; background:#F7F9FC; border-radius:12px; }
textarea, input { border-radius:10px !important; }

/* buttons */
.stButton > button, .stDownloadButton > button {
    border-radius:10px; font-weight:600; padding:.55rem 1rem; transition:background .15s, border-color .15s;
}
.stButton > button[kind="primary"] { background:#0F766E; border:1px solid #0F766E; color:#fff; }
.stButton > button[kind="primary"]:hover { background:#0B5E58; border-color:#0B5E58; }
.stDownloadButton > button { background:#fff; color:#1F2A44; border:1px solid #AEB9D0; }
.stDownloadButton > button:hover { border-color:#0F766E; color:#0F766E; }

/* the letter paper: the one memorable element */
.paper { background:#FFFFFF; border:1px solid #DCE2EC; border-radius:6px; padding:44px 52px;
         box-shadow:0 1px 2px rgba(31,42,68,.06), 0 12px 28px rgba(31,42,68,.10);
         font-family:'Lora', Georgia, serif; color:#1F2A44; font-size:1.02rem; line-height:1.75;
         min-height:430px; max-width:720px; margin:0 auto; }
.paper p { margin:0 0 1.05em 0; }
.paper.empty { color:#9AA5BD; }
.skel { height:11px; border-radius:6px; background:#EDF0F6; margin:0 0 14px 0; }
.chip { display:inline-block; padding:3px 11px; border-radius:99px; background:#E3F2F0; color:#0B5E58;
        font-size:.82rem; font-weight:500; margin-right:6px; }
.chip.warn { background:#FFF1D6; color:#8A5A00; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="app-header"><div class="app-logo">✉️</div><div>'
    '<div class="app-title">Cover Letter Generator</div>'
    '<div class="app-sub">Upload your resume, paste a job description and get a letter that sticks to your real experience.</div>'
    '</div></div>',
    unsafe_allow_html=True,
)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY not found. Copy .env.example to .env, add your Groq API key and restart the app.")
    st.stop()
client = Groq(api_key=api_key)


def paper_html(text: str) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return '<div class="paper">' + "".join(
        "<p>" + html.escape(p).replace("\n", "<br>") + "</p>" for p in paras
    ) + "</div>"


left, right = st.columns([1, 1.15], gap="large")

# ---------- Left: inputs ----------
with left:
    with st.container(border=True):
        st.markdown('<p class="section-title">Your details</p>', unsafe_allow_html=True)
        resume_file = st.file_uploader("Resume (PDF or TXT)", type=["pdf", "txt"])
        company = st.text_input("Company name", key="company", placeholder="e.g. Nordlicht Analytics")
        jd = st.text_area("Job description", key="jd", height=190,
                          placeholder="Paste the full job description here")
        c1, c2 = st.columns(2)
        tone = c1.selectbox("Tone", ["professional", "enthusiastic", "formal", "friendly but professional"])
        words = c2.slider("Length (words)", 150, 350, 250, step=10)

        resume_text = ""
        if resume_file is not None:
            if resume_file.name.lower().endswith(".pdf"):
                resume_text = extract_pdf_text(resume_file)
            else:
                resume_text = resume_file.read().decode("utf-8", errors="ignore")

        if resume_text:
            with st.expander("Check the text we read from your resume"):
                st.text(resume_text)

        generate = st.button("Generate cover letter", type="primary", use_container_width=True)

    if generate:
        if not (resume_text.strip() and jd.strip() and company.strip()):
            st.warning("Add a resume, the company name and the job description first.")
        elif len(resume_text) < 100:
            st.warning("We could not read enough text from this resume. Scanned PDFs are not supported; upload a text PDF or a TXT file.")
        else:
            with st.spinner("Writing your letter..."):
                try:
                    letter = generate_letter(client, resume_text, jd, company, tone, words)
                    st.session_state["letter_edit"] = letter
                    st.session_state["resume_used"] = resume_text
                    st.session_state["tone_used"] = tone
                except Exception as e:  # API limit, network, bad key
                    st.error(f"The LLM call failed: {e}")

# ---------- Right: the letter ----------
with right:
    if "letter_edit" not in st.session_state:
        st.markdown(
            '<div class="paper empty">'
            '<p style="color:#5B6785;font-style:italic;">Your letter will appear here.</p>'
            + "".join(f'<div class="skel" style="width:{w}%"></div>' for w in (92, 100, 84, 96, 70, 0, 100, 88, 94, 60))
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        text = st.session_state["letter_edit"]
        suspicious = unsupported_numbers(text, st.session_state.get("resume_used", ""))

        chips = f'<span class="chip">{word_count(text)} words</span>'
        chips += f'<span class="chip">{html.escape(st.session_state.get("tone_used", ""))}</span>'
        if suspicious:
            chips += '<span class="chip warn">check numbers</span>'
        st.markdown(chips, unsafe_allow_html=True)

        tab_preview, tab_edit = st.tabs(["Preview", "Edit text"])
        with tab_preview:
            st.markdown(paper_html(text), unsafe_allow_html=True)
        with tab_edit:
            st.text_area("Edit your letter", key="letter_edit", height=430, label_visibility="collapsed")

        if suspicious:
            st.warning(
                "These numbers are not in your resume. Check them before you send the letter: "
                + ", ".join(suspicious)
            )

        d1, d2 = st.columns(2)
        d1.download_button("Download .docx", letter_to_docx(text), "cover_letter.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
        d2.download_button("Download PDF", letter_to_pdf(text), "cover_letter.pdf",
                           "application/pdf", use_container_width=True)
