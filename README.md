# PS 42 – Cover Letter Generator

**Problem statement:** Writing a new cover letter for every job is tiring and students often send
generic ones. This app generates a tailored ~250-word cover letter from a resume (PDF/TXT) and a job
description, using only real resume details, and lets the user download it as `.docx` or `.pdf`.

## Features
- Resume upload (PDF or TXT) with a preview of the text that was read
- Company name, job description, tone and length controls
- Prompt forbids invented facts; the app also warns about numbers in the letter that are not in the resume
- Letter shown on a paper-style preview, with an Edit tab and word count
- Download the final letter as `.docx` or `.pdf`

## Tech
Python, Streamlit, Groq API (gpt-oss-120b), pypdf, python-docx, reportlab

## How to run

1. **Install the libraries**
   ```bash
   pip install -r requirements.txt
   ```
2. **Add your API key**
   - Get a free key at [console.groq.com](https://console.groq.com) (API Keys, then Create API Key).
   - In the project folder, create a new file named `.env`
     (or copy `.env.example` and rename the copy to `.env`).
   - Open `.env` and write this one line, using your own key:
     ```
     GROQ_API_KEY=your_key_here
     ```
   - The `.env` file stays on your computer and is not uploaded to GitHub.
3. **Start the app**
   ```bash
   streamlit run app.py
   ```
4. **Try it**: upload your resume, write the company name and the job description in the boxes, then click **Generate cover letter**.
5. **Save your letter**: click **Download .docx** or **Download PDF** to save the final cover letter on your computer.

## Project structure
```
app.py            Streamlit UI
utils.py          PDF reading, prompt, LLM call, .docx / .pdf export
sample_data/      5 fictional resume + job description pairs for testing
.streamlit/       Theme settings
requirements.txt  Libraries
.env.example      Template for the API key file (the real .env is not uploaded)
```

