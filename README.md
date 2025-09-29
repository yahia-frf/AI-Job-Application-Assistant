# 🤖 AI Job Application Assistant

**Polished demo**: upload a resume PDF, paste a job description, get a match score, tailored resume bullets, and a personalized cover letter — all exported in a single downloadable PDF package.

---

## 🔧 What this project does
- Extracts text from the uploaded resume PDF (PyPDF2)
- Uses **Google Gemini** to analyze job fit and produce JSON output (match score, missing skills, resume bullets, cover letter)
- Generates nice PDFs (resume appendix + cover letter) with **ReportLab**
- Merges original resume + AI-updated resume + cover letter into a single PDF for convenience
- Stylish Streamlit UI for recruiters / demo

---

