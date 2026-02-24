from flask import Flask, render_template, request
import os
from PyPDF2 import PdfReader
from markupsafe import escape
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_keywords(jobdesc):
    words = word_tokenize(jobdesc.lower())
    return list(set(w for w in words if w.isalpha() and w not in stopwords.words('english')))

def analyze_resume(text, job_keywords):
    score = 0
    matched_keywords = []
    missing_sections = []
    suggestions = []

    sections = ['education', 'experience', 'skills', 'projects']
    for sec in sections:
        if sec in text.lower():
            score += 20
        else:
            missing_sections.append(sec.capitalize())
            suggestions.append(f"Add {sec.capitalize()} section")

    for kw in job_keywords:
        if kw in text.lower():
            matched_keywords.append(kw)

    keyword_percent = int((len(matched_keywords) / len(job_keywords)) * 100) if job_keywords else 0
    score += int(keyword_percent * 0.2)

    if score > 100:
        score = 100

    return score, keyword_percent, matched_keywords, missing_sections, suggestions

def generate_pdf(score, keyword_percent, matched_keywords, missing_sections, suggestions):
    path = "static/Resume_Report.pdf"
    c = canvas.Canvas(path, pagesize=A4)

    y = 800
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "AI Resume Checker Report")

    c.setFont("Helvetica", 12)
    y -= 40
    c.drawString(50, y, f"ATS Score: {score}%")
    y -= 20
    c.drawString(50, y, f"Keyword Match: {keyword_percent}%")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Matched Keywords:")
    c.setFont("Helvetica", 11)
    y -= 20
    for kw in matched_keywords[:10]:
        c.drawString(60, y, f"- {kw}")
        y -= 15

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Missing Sections:")
    c.setFont("Helvetica", 11)
    y -= 20
    for sec in missing_sections:
        c.drawString(60, y, f"- {sec}")
        y -= 15

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Suggestions:")
    c.setFont("Helvetica", 11)
    y -= 20
    for s in suggestions:
        c.drawString(60, y, f"- {s}")
        y -= 15

    c.save()
    return path

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['resume']
    jobdesc = request.form.get('jobdesc', '')

    if file and allowed_file(file.filename):
        filename = escape(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        text = extract_text(filepath)
        job_keywords = extract_keywords(jobdesc)
        score, keyword_percent, matched_keywords, missing_sections, suggestions = analyze_resume(text, job_keywords)
        pdf_path = generate_pdf(score, keyword_percent, matched_keywords, missing_sections, suggestions)

        return render_template(
            'result.html',
            score=score,
            keyword_percent=keyword_percent,
            matched_keywords=matched_keywords,
            missing_sections=missing_sections,
            suggestions=suggestions,
            pdf_path=pdf_path
        )

    return "Invalid file format"

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
