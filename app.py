# app.py
import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
import os
import tempfile
from pdf_generator import (
    generate_resume_pdf,
    generate_cover_letter_pdf,
    merge_pdfs_as_single,
)

# ----------------------
# CONFIG
# ----------------------
GOOGLE_API_KEY = "your_api_key"  # <-- Replace with your Gemini API key
MODEL_NAME = "models/gemini-2.0-flash"  # or change if needed

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# ----------------------
# PAGE LAYOUT & STYLING
# ----------------------
st.set_page_config(page_title="AI Job Application Assistant", page_icon="🤖", layout="wide")

# Custom CSS for nicer look
st.markdown(
    """
    <style>
    .header {
        display:flex;
        align-items:center;
        gap:12px;
    }
    .app-title {
        font-size:28px;
        font-weight:700;
    }
    .muted { color: #6b7280; font-size:14px; }
    .card {
        background: linear-gradient(180deg, #ffffff 0%, #fbfbff 100%);
        padding:16px;
        border-radius:12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    }
    .green-btn button { background-color:#0f766e !important; color: white !important; }
    .accent { color: #0f766e; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
col1, col2 = st.columns([0.12, 0.88])
with col1:
    st.image("https://raw.githubusercontent.com/google/ground-0/main/images/logo.png", width=64)
with col2:
    st.markdown('<div class="header"><div><span class="app-title">AI Job Application Assistant</span><div class="muted">Analyze resumes vs job descriptions — get improved resume + cover letter PDFs</div></div></div>', unsafe_allow_html=True)

st.write("")  # spacer

# ----------------------
# Sidebar - Quick Help & Example
# ----------------------
with st.sidebar:
    st.markdown("## ⚙️ Quick Help")
    st.markdown(
        "- Upload a **resume PDF** (your full resume)\n"
        "- Paste the **job description** you want to apply for\n"
        "- Click **Analyze** → get JSON, improved resume and cover letter PDFs\n"
    )
    st.markdown("---")
    st.markdown("## 🧾 Example JD snippet")
    st.info("Data Engineer — SQL, Snowflake, dbt, AWS/Azure, data pipelines, data quality")

# ----------------------
# Main UI - Upload + Input
# ----------------------
st.markdown("### 1. Upload resume & paste job description")
col_a, col_b = st.columns([0.45, 0.55])

with col_a:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    name_input = st.text_input("Your name (for generated resume header)", value="Candidate Name")

with col_b:
    job_description = st.text_area("Paste Job Description here", height=220)
    extra_instructions = st.text_input("Optional: Add extra instructions for the assistant (tone, emphasize skills, etc.)", value="")

st.write("")  # spacer

# ----------------------
# Analyze Button
# ----------------------
analyze_col1, analyze_col2, analyze_col3 = st.columns([0.45, 0.3, 0.25])
with analyze_col2:
    analyze_clicked = st.button("🔎 Analyze", key="analyze_btn")

# ----------------------
# Helper: extract text from uploaded PDF
# ----------------------
def extract_text_from_pdf(file_obj):
    reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# ----------------------
# When analyze is clicked
# ----------------------
if analyze_clicked:
    if uploaded_file is None:
        st.warning("Please upload your resume PDF.")
    elif not job_description.strip():
        st.warning("Please paste the job description.")
    else:
        with st.spinner("Extracting resume text..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        # Build prompt (structured)
        system_prompt = f"""
You are an assistant that compares a candidate's resume to a job description.
Return a clean JSON object with the following keys:
- job_title (string)
- company (string)
- match_score (0-100 integer)
- top_matches (list of strings)  // skills found in both resume and job description
- missing_skills (list of strings) // skills the job requires but are missing or weak in resume
- resume_bullets_to_add (list of strings) // 3-6 tailored resume bullets that the candidate can add
- personalized_cover_letter (string) // a professional 3-paragraph cover letter tailored to the company and job title
"""

        user_prompt = f"""
Job Description:
{job_description}

Resume:
{resume_text}

Extra instructions:
{extra_instructions}

Please produce only valid JSON. When unsure about company or job title put empty strings.
"""

        full_prompt = system_prompt + "\n" + user_prompt

        with st.spinner("Contacting Gemini and generating analysis..."):
            try:
                response = model.generate_content(full_prompt)
                raw_text = response.text.strip()
            except Exception as e:
                st.error(f"Error calling Gemini: {e}")
                raw_text = None

        if raw_text:
            # Try to clean code fences and parse JSON
            cleaned = raw_text.replace("```json", "").replace("```", "").strip()
            parsed = None
            try:
                parsed = json.loads(cleaned)
            except Exception:
                # attempt to find first { ... } substring
                try:
                    start = cleaned.index("{")
                    end = cleaned.rindex("}") + 1
                    candidate = cleaned[start:end]
                    parsed = json.loads(candidate)
                except Exception as e:
                    st.error("Failed to parse JSON output from the model. Showing raw output below.")
                    st.code(raw_text)
                    parsed = None

            if parsed:
                st.success("✅ Analysis complete")
                # SHOW summary card
                score = int(parsed.get("match_score", 0))
                job_title = parsed.get("job_title", "")
                company = parsed.get("company", "")

                # Top row: score and job
                c1, c2, c3 = st.columns([0.25, 0.5, 0.25])
                with c1:
                    st.metric(label="Match Score", value=f"{score} / 100")
                    st.progress(min(max(score, 0), 100))
                with c2:
                    st.markdown(f"### {job_title or 'Job Title not provided'}")
                    st.markdown(f"**Company:** {company or '—'}")
                    st.write("")
                with c3:
                    st.write("")  # spacing
                    st.write("")

                # Two columns: Matches & Missing
                st.markdown("### 🔎 Skills")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.subheader("Top Matches")
                    for s in parsed.get("top_matches", []):
                        st.markdown(f"- ✅ {s}")
                with col_m2:
                    st.subheader("Missing / Weak Skills")
                    for s in parsed.get("missing_skills", []):
                        st.markdown(f"- ⚠️ {s}")

                # Resume bullets suggestions card
                st.markdown("### ✍️ Suggested resume bullets to add")
                st.markdown('<div class="card">', unsafe_allow_html=True)
                bullets = parsed.get("resume_bullets_to_add", [])
                for b in bullets:
                    st.markdown(f"- {b}")
                st.markdown('</div>', unsafe_allow_html=True)

                # Cover letter preview (collapsible)
                st.markdown("### 📨 Personalized Cover Letter")
                with st.expander("Preview cover letter"):
                    st.write(parsed.get("personalized_cover_letter", ""))

                # Offer downloads: generate PDFs
                st.markdown("### 📄 Generate PDFs")
                os.makedirs("outputs", exist_ok=True)

                # Make temporary files for pdf outputs
                temp_dir = tempfile.mkdtemp()
                ai_resume_path = os.path.join(temp_dir, "ai_resume.pdf")
                ai_cover_path = os.path.join(temp_dir, "ai_cover_letter.pdf")
                merged_final_path = os.path.join(temp_dir, "final_package.pdf")

                try:
                    # Create AI-generated resume pdf (new bullets appended)
                    generate_resume_pdf(
                        ai_resume_path,
                        name_input or "Candidate",
                        resume_text,
                        parsed.get("resume_bullets_to_add", []),
                    )
                    # Create cover letter pdf
                    generate_cover_letter_pdf(
                        ai_cover_path,
                        parsed.get("company", "Company"),
                        parsed.get("personalized_cover_letter", ""),
                    )
                    # Merge uploaded original resume + ai_resume + cover into single final pdf
                    # Get the original uploaded file again (seek back)
                    uploaded_file.seek(0)
                    original_bytes = uploaded_file.read()
                    # Save uploaded file to temp
                    orig_path = os.path.join(temp_dir, "original_resume.pdf")
                    with open(orig_path, "wb") as f:
                        f.write(original_bytes)

                    merge_pdfs_as_single([orig_path, ai_resume_path, ai_cover_path], merged_final_path)

                    st.success("✅ PDFs generated")

                    # Download buttons
                    with open(merged_final_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Full Package (Original + AI Resume + Cover Letter)",
                            data=f,
                            file_name="ai_job_package.pdf",
                            mime="application/pdf",
                        )
                    # Also provide separate downloads
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        with open(ai_resume_path, "rb") as f:
                            st.download_button("📥 Download AI Resume (PDF)", f, file_name="ai_resume.pdf")
                    with col_d2:
                        with open(ai_cover_path, "rb") as f:
                            st.download_button("📥 Download Cover Letter (PDF)", f, file_name="cover_letter.pdf")

                except Exception as e:
                    st.error(f"Error generating PDFs: {e}")
            # end if parsed
# end if analyze_clicked

# Footer
st.markdown("---")
st.markdown("Built by **Yahia FERARSA** • GitHub-ready • Replace `YOUR_API_KEY` with your Gemini key")
