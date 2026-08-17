# AI Recruiter - Intelligent Resume Screening & Candidate Ranking Platform

A production-grade, local **AI Recruiter** web application designed to help recruiters screen, parse, analyze, and rank candidate resumes against job requisitions using rule-based scoring and NLP.

![AI Recruiter Dashboard](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.24+-2563EB)
![spaCy](https://img.shields.io/badge/spaCy-NLP-09A3D5?logo=spacy)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn)
![Zero Paid APIs](https://img.shields.io/badge/Cost-100%25%20Local-10B981)

---

## 🌟 Key Features

1. **Batch Resume Ingestion (PyMuPDF)**
   - Upload single or multiple PDF candidate resumes simultaneously.
   - Robust text normalization, ligature handling, and empty/scanned PDF detection.
   - Graceful handling of corrupted or password-protected files with user-friendly error banners.

2. **Intelligent Information Extraction**
   - **Candidate Name**: spaCy NER `PERSON` entity extraction + layout header heuristics.
   - **Contact Details**: High-precision regex for Email, Phone Number, LinkedIn, GitHub, and Portfolio URLs.
   - **600+ Skill Taxonomy Engine**: Categorized into Programming Languages, Frameworks, Cloud & DevOps, Databases, AI/ML, and Tools.
   - **Experience Parser**: Automatically calculates total years of professional experience from date ranges and timelines.
   - **Education & Certifications**: Extracts degrees (B.S., M.S., Ph.D., MBA), universities, graduation years, and certifications (AWS, Kubernetes CKA, Scrum Master, PMP).

3. **Transparent 60/20/20 Matcher Engine**
   - **60% Skills Match**:
     - *Required Skills (45-60%)*: Strict matching with alias resolution (e.g. `K8s` -> `Kubernetes`, `Postgres` -> `PostgreSQL`).
     - *Preferred Skills (15%)*: Nice-to-have bonus technical capabilities.
   - **20% Experience Relevance**:
     - Evaluates candidate years against required minimums (full score if met/exceeded, proportional score if below).
   - **20% Context & Keyword Similarity**:
     - TF-IDF Vectorization and Cosine Similarity between the candidate resume text and target job description.
   - **Categorization**:
     - 🌟 **Excellent Match** ($\ge 80\%$)
     - 🔷 **Good Match** ($65\% - 79\%$)
     - 🟡 **Moderate Match** ($50\% - 64\%$)
     - 🔴 **Low Match** ($< 50\%$)

4. **Interactive Recruiter Dashboard**
   - Summary KPI cards: Total Resumes, Suitable Candidates, Average Score, Top Score.
   - Dynamic Altair score distribution charts and category donuts.
   - Skill supply vs skill gap analysis across candidate pool.

5. **Candidate Hub & Deep Dive Profile**
   - Real-time search and multi-criteria filters (Category, Score slider, Specific skill tags).
   - Candidate Deep Dive drawer with score gauges, contact info, matching vs missing skill badges, experience timeline, education, and raw text inspector.

6. **Job Requisition Manager**
   - Pre-loaded templates for **Senior Python Backend**, **Full Stack React/Node**, **DevOps Cloud Architect**, and **Data Scientist**.
   - Custom job requisition creator with 1-click automatic skill extraction from free-text job descriptions.

7. **Reports, Export & Comparison**
   - Head-to-Head Candidate Comparison Matrix (compare 2-3 candidates side-by-side).
   - Export candidate pool rankings as formatted **CSV** spreadsheet.
   - Export full ATS structured payload as **JSON**.
   - Generate individual candidate evaluation report cards as printable **Markdown**.

---

## 🏗️ Project Architecture

```
AI-Recruiter/
├── app.py                     # Main Streamlit web application
├── requirements.txt           # Production dependencies
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Cache and OS ignore rules
│
├── data/
│   ├── sample_resumes/        # 6 Pre-generated realistic test PDF resumes
│   └── default_jobs.json      # Pre-loaded job templates
│
├── models/
│   ├── __init__.py
│   ├── candidate.py           # Dataclass models: CandidateProfile, Education, Experience
│   ├── job.py                 # Dataclass models: JobDescription, MatchResult
│   └── nlp_model.py           # spaCy loader, fallback tokenizers, entity & TF-IDF extractors
│
├── services/
│   ├── __init__.py
│   ├── pdf_extractor.py       # PyMuPDF text extractor with stream & error handling
│   ├── resume_parser.py       # Full extraction pipeline (600+ skills, contact, experience)
│   ├── job_parser.py          # Job description requirement normalizer & auto-extractor
│   ├── matcher.py             # Transparent 60/20/20 rule-based scoring engine
│   └── ranking.py             # Candidate ranking, multi-filter, and analytics aggregator
│
├── utils/
│   ├── __init__.py
│   ├── validators.py          # PDF header, file size, and form validators
│   └── exporters.py           # CSV, JSON, and evaluation report generators
│
├── assets/
│   ├── styles.css             # Polished UI theme, glassmorphism cards, glowing badges
│   └── sample_generator.py    # Script to regenerate realistic sample PDF resumes
│
└── tests/
    ├── __init__.py
    ├── test_pdf_extractor.py  # Unit tests for PDF parsing
    ├── test_resume_parser.py  # Unit tests for contact, skill, and experience extraction
    ├── test_matcher.py        # Unit tests for scoring logic & edge cases
    └── test_exporters.py      # Unit tests for CSV & JSON exports
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Installation

Clone the repository and install the dependencies:

```bash
# Navigate to project directory
cd AI-Recruiter

# Install dependencies
pip install -r requirements.txt

# Download the spaCy English NLP model
python -m spacy download en_core_web_sm
```

*(Note: If spaCy model download is restricted in your environment, the application will automatically fall back to its built-in high-performance regex & scikit-learn NLP engine without crashing!)*

### 3. Generate Sample Resumes (Optional)

6 realistic candidate PDF resumes are included in `data/sample_resumes/`. You can regenerate them at any time:

```bash
python assets/sample_generator.py
```

### 4. Run the Web Application

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

---

## 🧪 Running the Test Suite

Run all automated unit tests using Python's standard `unittest`:

```bash
python -m unittest discover tests -v
```

---

## 📊 Transparent Matching Formula

$$\text{Overall Score} = \text{Skills Score (60 pts)} + \text{Experience Score (20 pts)} + \text{Context Relevance (20 pts)}$$

| Component | Weight | Calculation Method |
| :--- | :---: | :--- |
| **Required Skills** | $45\%$ | $\frac{\text{Matching Required Skills}}{\text{Total Required Skills}} \times 45$ |
| **Preferred Skills** | $15\%$ | $\frac{\text{Matching Preferred Skills}}{\text{Total Preferred Skills}} \times 15$ |
| **Experience Relevance** | $20\%$ | If $\text{Candidate Exp} \ge \text{Target Exp} \implies 20\text{ pts}$; else $\frac{\text{Candidate Exp}}{\text{Target Exp}} \times 20$ |
| **Context & Keyword Similarity** | $20\%$ | $\text{Cosine Similarity}(\text{TF-IDF}_{\text{Resume}}, \text{TF-IDF}_{\text{JD}}) \times 20$ |

---

## 📄 License
MIT License. Built for local, privacy-friendly, and cost-free recruitment workflow optimization.
