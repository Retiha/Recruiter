"""AI Recruiter - Intelligent Candidate Resume Screening & Ranking Platform."""
import io
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import streamlit as st
import altair as alt

from models.candidate import CandidateProfile
from models.job import JobDescription, MatchResult
from models.nlp_model import get_nlp_engine
from services.pdf_extractor import PDFExtractor
from services.resume_parser import ResumeParser, SKILLS_TAXONOMY
from services.job_parser import JobParser
from services.matcher import CandidateJobMatcher
from services.ranking import CandidateRanker
from utils.validators import PDFValidator, JobValidator
from utils.exporters import DataExporter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_recruiter.app")

# Page Configuration
st.set_page_config(
    page_title="AI Recruiter | Resume Screening & Candidate Matching",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Default Jobs Path
DATA_DIR = Path(__file__).parent / "data"
DEFAULT_JOBS_FILE = DATA_DIR / "default_jobs.json"
SAMPLE_RESUMES_DIR = DATA_DIR / "sample_resumes"


def load_default_jobs() -> List[Dict[str, Any]]:
    """Loads pre-configured job requisitions."""
    if DEFAULT_JOBS_FILE.exists():
        try:
            with open(DEFAULT_JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load default jobs: {e}")
    return []


# Initialize Session State
if "candidates" not in st.session_state:
    st.session_state.candidates = {}  # Dict[candidate_id, CandidateProfile]

if "job_templates" not in st.session_state:
    st.session_state.job_templates = load_default_jobs()

if "current_job" not in st.session_state:
    # Default to first job template if available
    if st.session_state.job_templates:
        default_tpl = st.session_state.job_templates[0]
        st.session_state.current_job = JobDescription(
            id=default_tpl["id"],
            title=default_tpl["title"],
            description=default_tpl["description"],
            required_skills=default_tpl["required_skills"],
            preferred_skills=default_tpl.get("preferred_skills", []),
            min_experience_years=float(default_tpl.get("min_experience_years", 3.0)),
            seniority_level=default_tpl.get("seniority_level", "Senior")
        )
    else:
        st.session_state.current_job = JobDescription(
            id="job_custom",
            title="Senior Software Engineer",
            description="We are seeking a senior software engineer...",
            required_skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
            preferred_skills=["AWS", "Kubernetes"],
            min_experience_years=4.0
        )

if "active_nav" not in st.session_state:
    st.session_state.active_nav = "📊 Dashboard"

if "selected_candidate_id" not in st.session_state:
    st.session_state.selected_candidate_id = None


# Helpers for UI Rendering
def get_badge_html(category: str) -> str:
    cat_class = "badge-low"
    if category == "Excellent Match":
        cat_class = "badge-excellent"
    elif category == "Good Match":
        cat_class = "badge-good"
    elif category == "Moderate Match":
        cat_class = "badge-moderate"
    return f'<span class="badge {cat_class}">{category}</span>'


def render_skill_chips(skills: List[str], skill_type: str = "matched") -> str:
    if not skills:
        return '<span style="color:#94A3B8; font-size:0.85rem;">None</span>'
    
    chip_class = "skill-tag-matched"
    if skill_type == "missing":
        chip_class = "skill-tag-missing"
    elif skill_type == "extra":
        chip_class = "skill-tag-extra"

    html = "".join([f'<span class="skill-tag {chip_class}">{s}</span>' for s in skills])
    return html


# Recalculate matches for current candidate pool
def evaluate_candidates() -> List[MatchResult]:
    cands = list(st.session_state.candidates.values())
    if not cands:
        return []
    return CandidateJobMatcher.match_all(cands, st.session_state.current_job)


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/talent.png", width=60)
    st.title("AI Recruiter")
    st.caption("Intelligent Resume Screening & Ranking Platform")
    st.markdown("---")

    nav_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "⚡ Resume Screening",
            "👥 Candidates",
            "💼 Job Description",
            "📈 Reports & Compare"
        ],
        index=["📊 Dashboard", "⚡ Resume Screening", "👥 Candidates", "💼 Job Description", "📈 Reports & Compare"].index(st.session_state.active_nav)
    )
    st.session_state.active_nav = nav_selection

    st.markdown("---")
    
    # Active Target Job Status Widget
    st.markdown("##### 🎯 Active Target Role")
    st.info(f"**{st.session_state.current_job.title}**\n\nMin Exp: {st.session_state.current_job.min_experience_years} yrs\n\nReq Skills: {len(st.session_state.current_job.required_skills)}")

    # Pool Status
    st.markdown(f"**Resumes in Pool:** `{len(st.session_state.candidates)}`")

    # NLP Status
    nlp_eng = get_nlp_engine()
    if nlp_eng.is_spacy_available:
        st.success("NLP Engine: spaCy en_core_web_sm active")
    else:
        st.info("NLP Engine: High-Performance Regex & Scikit-Learn")


# ==========================================
# VIEW: 📊 RECRUITER DASHBOARD
# ==========================================
if st.session_state.active_nav == "📊 Dashboard":
    st.markdown(
        f"""
        <div class="recruiter-header">
            <h1>Recruitment Analytics Dashboard</h1>
            <p>Target Role: <strong>{st.session_state.current_job.title}</strong> &nbsp;|&nbsp; 
               Seniority: <strong>{st.session_state.current_job.seniority_level}</strong> &nbsp;|&nbsp; 
               Required Experience: <strong>{st.session_state.current_job.min_experience_years} Years</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    match_results = evaluate_candidates()
    metrics = CandidateRanker.calculate_dashboard_metrics(match_results, st.session_state.current_job)
    ranked_candidates = CandidateRanker.rank_candidates(match_results)

    # Top KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Resumes</div>
                <div class="kpi-value">{metrics['total_resumes']}</div>
                <div class="kpi-subtitle">Screened Profiles</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Suitable Candidates</div>
                <div class="kpi-value">{metrics['suitable_candidates']}</div>
                <div class="kpi-subtitle">{metrics['suitable_percentage']}% of total pool</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Average Match</div>
                <div class="kpi-value">{metrics['average_score']}%</div>
                <div class="kpi-subtitle">Candidate Pool Mean</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Highest Match</div>
                <div class="kpi-value">{metrics['highest_score']}%</div>
                <div class="kpi-subtitle">Top Performer Score</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if not match_results:
        st.warning("⚠️ No resumes loaded yet. Go to **⚡ Resume Screening** to upload candidate PDFs or load the pre-built sample dataset!")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🚀 Load Sample Resumes", type="primary"):
                # Load sample resumes
                parser = ResumeParser()
                sample_files = list(SAMPLE_RESUMES_DIR.glob("*.pdf")) if SAMPLE_RESUMES_DIR.exists() else []
                loaded_count = 0
                for fpath in sample_files:
                    ext_res = PDFExtractor.extract_text(fpath)
                    if ext_res.success:
                        profile = parser.parse(ext_res.text, file_name=ext_res.file_name, file_size_kb=ext_res.file_size_kb)
                        st.session_state.candidates[profile.id] = profile
                        loaded_count += 1
                st.success(f"Successfully loaded {loaded_count} sample candidate resumes!")
                st.rerun()
    else:
        # Charts & Analytics
        c_left, c_right = st.columns([3, 2])

        with c_left:
            st.markdown("#### 📈 Candidate Score Distribution")
            chart_df = pd.DataFrame([
                {"Candidate": r["candidate_name"], "Score": r["overall_score"], "Category": r["category"]}
                for r in ranked_candidates
            ])

            bar_chart = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("Candidate:N", sort="-y", title="Candidate"),
                y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Match Score (%)"),
                color=alt.Color(
                    "Category:N",
                    scale=alt.Scale(
                        domain=["Excellent Match", "Good Match", "Moderate Match", "Low Match"],
                        range=["#10B981", "#3B82F6", "#F59E0B", "#EF4444"]
                    ),
                    legend=alt.Legend(title="Match Category")
                ),
                tooltip=["Candidate", "Score", "Category"]
            ).properties(height=280)

            st.altair_chart(bar_chart, use_container_width=True)

        with c_right:
            st.markdown("#### 🎯 Match Category Breakdown")
            cat_df = pd.DataFrame(
                list(metrics["category_counts"].items()),
                columns=["Category", "Count"]
            )
            cat_df = cat_df[cat_df["Count"] > 0]
            if not cat_df.empty:
                donut_chart = alt.Chart(cat_df).mark_arc(innerRadius=45).encode(
                    theta=alt.Theta("Count:Q"),
                    color=alt.Color(
                        "Category:N",
                        scale=alt.Scale(
                            domain=["Excellent Match", "Good Match", "Moderate Match", "Low Match"],
                            range=["#10B981", "#3B82F6", "#F59E0B", "#EF4444"]
                        )
                    ),
                    tooltip=["Category", "Count"]
                ).properties(height=280)
                st.altair_chart(donut_chart, use_container_width=True)
            else:
                st.info("No categorical data available.")

        # Top Ranking Leaderboard
        st.markdown("---")
        st.markdown("### 🏆 Top Candidate Leaderboard")

        leaderboard_data = []
        for c in ranked_candidates:
            match_skills = c["matching_required_skills"] + c["matching_preferred_skills"]
            miss_skills = c["missing_required_skills"] + c["missing_preferred_skills"]
            leaderboard_data.append({
                "Rank": c["rank"],
                "Candidate Name": c["candidate_name"],
                "Email": c["email"],
                "Match Score": f"{c['overall_score']}%",
                "Category": c["category"],
                "Skills Score": f"{c['skills_score']} / 60",
                "Experience": f"{c['candidate_experience_years']} yrs",
                "Matched Skills": len(match_skills),
                "Missing Skills": len(miss_skills)
            })

        st.dataframe(
            pd.DataFrame(leaderboard_data),
            use_container_width=True,
            hide_index=True
        )

        # Skill Demand vs Gap Breakdown
        st.markdown("---")
        col_sk1, col_sk2 = st.columns(2)
        with col_sk1:
            st.markdown("#### 🟢 Most Common Matched Skills in Pool")
            if metrics["top_matching_skills"]:
                top_m_df = pd.DataFrame(metrics["top_matching_skills"], columns=["Skill", "Candidates"])
                m_bar = alt.Chart(top_m_df).mark_bar(color="#10B981").encode(
                    x=alt.X("Candidates:Q", title="Number of Candidates"),
                    y=alt.Y("Skill:N", sort="-x", title="Skill"),
                    tooltip=["Skill", "Candidates"]
                ).properties(height=240)
                st.altair_chart(m_bar, use_container_width=True)
            else:
                st.info("No matching skill statistics available.")

        with col_sk2:
            st.markdown("#### 🔴 Most Frequent Missing Skills (Skill Gaps)")
            if metrics["top_missing_skills"]:
                top_miss_df = pd.DataFrame(metrics["top_missing_skills"], columns=["Skill", "Candidates Missing"])
                miss_bar = alt.Chart(top_miss_df).mark_bar(color="#EF4444").encode(
                    x=alt.X("Candidates Missing:Q", title="Number of Candidates Missing"),
                    y=alt.Y("Skill:N", sort="-x", title="Skill"),
                    tooltip=["Skill", "Candidates Missing"]
                ).properties(height=240)
                st.altair_chart(miss_bar, use_container_width=True)
            else:
                st.info("No skill gaps identified across pool.")


# ==========================================
# VIEW: ⚡ RESUME SCREENING
# ==========================================
elif st.session_state.active_nav == "⚡ Resume Screening":
    st.markdown(
        """
        <div class="recruiter-header">
            <h1>Batch Resume Screening</h1>
            <p>Upload single or multiple PDF candidate resumes to parse details and evaluate against job requirements.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_upload, col_actions = st.columns([3, 1])

    with col_upload:
        uploaded_files = st.file_uploader(
            "Upload Candidate Resumes (PDF)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Select one or multiple PDF resumes to screen."
        )

    with col_actions:
        st.markdown("##### ⚡ Quick Actions")
        if st.button("📂 Load 6 Sample Resumes", type="primary", use_container_width=True):
            parser = ResumeParser()
            sample_files = list(SAMPLE_RESUMES_DIR.glob("*.pdf")) if SAMPLE_RESUMES_DIR.exists() else []
            count = 0
            for fpath in sample_files:
                ext_res = PDFExtractor.extract_text(fpath)
                if ext_res.success:
                    profile = parser.parse(ext_res.text, file_name=ext_res.file_name, file_size_kb=ext_res.file_size_kb)
                    st.session_state.candidates[profile.id] = profile
                    count += 1
            st.success(f"Loaded {count} sample resumes into candidate pool!")
            st.rerun()

        if st.button("🗑️ Clear Candidate Pool", use_container_width=True):
            st.session_state.candidates = {}
            st.session_state.selected_candidate_id = None
            st.info("Candidate pool cleared.")
            st.rerun()

    # Process Uploaded Files
    if uploaded_files:
        parser = ResumeParser()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        parsed_this_batch = 0
        error_logs = []

        for i, file_obj in enumerate(uploaded_files):
            status_text.text(f"Processing ({i+1}/{len(uploaded_files)}): {file_obj.name}...")
            progress_bar.progress(int(((i + 1) / len(uploaded_files)) * 100))

            # 1. Validate File
            is_valid, val_err = PDFValidator.validate_file(file_obj)
            if not is_valid:
                error_logs.append(f"❌ {file_obj.name}: {val_err}")
                continue

            # 2. Extract Text via PyMuPDF
            ext_result = PDFExtractor.extract_text(file_obj)
            if not ext_result.success:
                error_logs.append(f"❌ {file_obj.name}: {ext_result.error_message}")
                continue

            if ext_result.is_empty:
                error_logs.append(f"⚠️ {file_obj.name}: File is empty or a scanned image with no selectable text.")
                continue

            # 3. Parse Resume
            profile = parser.parse(
                text=ext_result.text,
                file_name=ext_result.file_name,
                file_size_kb=ext_result.file_size_kb
            )
            st.session_state.candidates[profile.id] = profile
            parsed_this_batch += 1

        status_text.empty()
        progress_bar.empty()

        if parsed_this_batch > 0:
            st.success(f"✅ Successfully extracted and processed {parsed_this_batch} resumes!")

        if error_logs:
            with st.expander("⚠️ Processing Warnings & Errors", expanded=True):
                for err in error_logs:
                    st.error(err)

    # Currently Loaded Resumes Table
    st.markdown("---")
    st.markdown(f"### 📋 Resumes in Active Pool ({len(st.session_state.candidates)})")

    if st.session_state.candidates:
        rows = []
        for cand in st.session_state.candidates.values():
            rows.append({
                "ID": cand.id,
                "File Name": cand.file_name,
                "Candidate Name": cand.name,
                "Email": cand.email or "—",
                "Phone": cand.phone or "—",
                "Experience": f"{cand.total_experience_years} yrs",
                "Skills Detected": len(cand.all_skills),
                "File Size": f"{cand.file_size_kb} KB"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No candidate resumes in pool. Upload resumes above or click 'Load 6 Sample Resumes'.")


# ==========================================
# VIEW: 👥 CANDIDATES HUB & DEEP DIVE
# ==========================================
elif st.session_state.active_nav == "👥 Candidates":
    st.markdown(
        f"""
        <div class="recruiter-header">
            <h1>Candidate Screening & Profile Deep Dive</h1>
            <p>Search, filter, and inspect detailed skill alignments, experience timelines, and matching breakdowns.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    match_results = evaluate_candidates()

    if not match_results:
        st.warning("⚠️ No candidates loaded. Please go to **⚡ Resume Screening** and upload resumes or load sample data.")
    else:
        # Search & Filtering Toolbar
        st.markdown("#### 🔍 Search & Filters")
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1.5, 1.5, 2])

        with f_col1:
            search_query = st.text_input("Search Candidate", placeholder="Filter by name or email...", key="search_cand_input")

        with f_col2:
            selected_categories = st.multiselect(
                "Match Category",
                options=["Excellent Match", "Good Match", "Moderate Match", "Low Match"],
                default=["Excellent Match", "Good Match", "Moderate Match", "Low Match"]
            )

        with f_col3:
            min_score_filter = st.slider("Min Match Score (%)", min_value=0, max_value=100, value=0, step=5)

        with f_col4:
            all_pool_skills = sorted(list(set(
                s for c in st.session_state.candidates.values() for s in c.all_skills
            )))
            skill_filter = st.multiselect("Must Have Skill(s)", options=all_pool_skills)

        # Apply Filters
        filtered_results = CandidateRanker.filter_candidates(
            results=match_results,
            query=search_query,
            categories=selected_categories,
            min_score=float(min_score_filter),
            required_skill_filter=skill_filter,
            candidate_profiles=st.session_state.candidates
        )
        ranked_filtered = CandidateRanker.rank_candidates(filtered_results)

        st.caption(f"Showing {len(ranked_filtered)} of {len(match_results)} candidates")

        # Candidate Table
        if ranked_filtered:
            table_records = []
            for r in ranked_filtered:
                table_records.append({
                    "Rank": r["rank"],
                    "Name": r["candidate_name"],
                    "Email": r["email"] or "N/A",
                    "Score (%)": r["overall_score"],
                    "Category": r["category"],
                    "Skills Match": f"{r['skills_score']}/60",
                    "Experience": f"{r['candidate_experience_years']} yrs",
                    "Matching Skills": len(r["matching_required_skills"]) + len(r["matching_preferred_skills"]),
                    "Missing Skills": len(r["missing_required_skills"]) + len(r["missing_preferred_skills"])
                })
            
            st.dataframe(
                pd.DataFrame(table_records),
                use_container_width=True,
                hide_index=True
            )

            # Candidate Profile Deep Dive
            st.markdown("---")
            st.markdown("### 🔎 Detailed Candidate Evaluation")

            # Selection dropdown
            cand_names = {r["candidate_id"]: f"#{r['rank']} {r['candidate_name']} ({r['overall_score']}%)" for r in ranked_filtered}
            selected_id = st.selectbox(
                "Select Candidate to Inspect",
                options=list(cand_names.keys()),
                format_func=lambda cid: cand_names[cid]
            )

            if selected_id and selected_id in st.session_state.candidates:
                candidate = st.session_state.candidates[selected_id]
                match_res = next((r for r in match_results if r.candidate_id == selected_id), None)

                if match_res:
                    # Candidate Header Card
                    st.markdown(
                        f"""
                        <div class="candidate-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <div>
                                    <div class="candidate-name">{candidate.name}</div>
                                    <div style="color: #64748B; margin-top: 4px;">
                                        📧 {candidate.email or 'No email'} &nbsp;|&nbsp; 
                                        📞 {candidate.phone or 'No phone'} &nbsp;|&nbsp;
                                        📄 {candidate.file_name} ({candidate.file_size_kb} KB)
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="candidate-score-ring">{match_res.overall_score}%</div>
                                    <div>{get_badge_html(match_res.category)}</div>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Links Bar
                    if candidate.links:
                        links_html = []
                        if "linkedin" in candidate.links:
                            links_html.append(f"[🔗 LinkedIn]({candidate.links['linkedin']})")
                        if "github" in candidate.links:
                            links_html.append(f"[💻 GitHub]({candidate.links['github']})")
                        if "portfolio" in candidate.links:
                            links_html.append(f"[🌐 Portfolio]({candidate.links['portfolio']})")
                        st.markdown(" &nbsp;•&nbsp; ".join(links_html))

                    # Score Breakdown Columns
                    st.markdown("#### 🎯 Score Component Breakdown")
                    sb1, sb2, sb3 = st.columns(3)
                    with sb1:
                        st.metric(
                            label="🛠️ Skills Match (60% Max)",
                            value=f"{match_res.skills_score} / 60.0",
                            delta=f"{len(match_res.matching_required_skills)}/{len(st.session_state.current_job.required_skills)} Required Skills"
                        )
                    with sb2:
                        exp_delta = f"{match_res.candidate_experience_years - match_res.required_experience_years:+.1f} yrs vs required" if match_res.required_experience_years > 0 else "Requirement met"
                        st.metric(
                            label="⏳ Experience Relevance (20% Max)",
                            value=f"{match_res.experience_score} / 20.0",
                            delta=exp_delta
                        )
                    with sb3:
                        st.metric(
                            label="🧠 Context & Keyword Similarity (20% Max)",
                            value=f"{match_res.similarity_score} / 20.0",
                            delta="TF-IDF Cosine Match"
                        )

                    # Detailed Skills Section
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### 🧩 Skills Analysis")
                    sk_col1, sk_col2, sk_col3 = st.columns(3)

                    with sk_col1:
                        st.markdown(f"**🟢 Matching Required Skills ({len(match_res.matching_required_skills)})**")
                        st.markdown(render_skill_chips(match_res.matching_required_skills, "matched"), unsafe_allow_html=True)
                        if match_res.matching_preferred_skills:
                            st.markdown(f"<br>**🟢 Matching Preferred Skills ({len(match_res.matching_preferred_skills)})**", unsafe_allow_html=True)
                            st.markdown(render_skill_chips(match_res.matching_preferred_skills, "matched"), unsafe_allow_html=True)

                    with sk_col2:
                        st.markdown(f"**🔴 Missing Required Skills ({len(match_res.missing_required_skills)})**")
                        st.markdown(render_skill_chips(match_res.missing_required_skills, "missing"), unsafe_allow_html=True)
                        if match_res.missing_preferred_skills:
                            st.markdown(f"<br>**🟠 Missing Preferred Skills ({len(match_res.missing_preferred_skills)})**", unsafe_allow_html=True)
                            st.markdown(render_skill_chips(match_res.missing_preferred_skills, "missing"), unsafe_allow_html=True)

                    with sk_col3:
                        st.markdown(f"**🔵 Additional Candidate Skills ({len(match_res.additional_skills)})**")
                        st.markdown(render_skill_chips(match_res.additional_skills[:12], "extra"), unsafe_allow_html=True)

                    # Strengths & Improvement Areas
                    st.markdown("---")
                    fb1, fb2 = st.columns(2)
                    with fb1:
                        st.markdown("#### 💡 Key Strengths")
                        for s in match_res.strengths:
                            st.markdown(f"- ✅ {s}")
                    with fb2:
                        st.markdown("#### ⚠️ Potential Gaps / Review Areas")
                        for imp in match_res.improvement_areas:
                            st.markdown(f"- 🔸 {imp}")

                    # Detailed Tabs: Experience, Education, Full Resume Text
                    st.markdown("---")
                    t_exp, t_edu, t_proj, t_text = st.tabs(["💼 Work Experience", "🎓 Education & Certifications", "🚀 Projects", "📄 Raw Resume Text"])

                    with t_exp:
                        st.markdown(f"**Total Professional Experience:** `{candidate.total_experience_years} Years`")
                        if candidate.experience:
                            for exp in candidate.experience:
                                with st.container():
                                    st.markdown(f"**{exp.title}** &nbsp;•&nbsp; *{exp.company}*")
                                    if exp.date_range:
                                        st.caption(f"🗓️ {exp.date_range} ({exp.duration_years} yrs)")
                                    if exp.highlights:
                                        for h in exp.highlights:
                                            st.markdown(f"- {h}")
                                    st.markdown("---")
                        else:
                            st.info("No structured experience entries parsed. Check raw text tab.")

                    with t_edu:
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            st.markdown("##### 🎓 Education")
                            if candidate.education:
                                for edu in candidate.education:
                                    st.markdown(f"- **{edu.degree}**")
                                    st.markdown(f"  *{edu.institution}* {f'({edu.year})' if edu.year else ''}")
                            else:
                                st.write("No education details detected.")
                        
                        with col_e2:
                            st.markdown("##### 📜 Certifications")
                            if candidate.certifications:
                                for cert in candidate.certifications:
                                    st.markdown(f"- 🏅 {cert}")
                            else:
                                st.write("No certifications detected.")

                    with t_proj:
                        if candidate.projects:
                            for proj in candidate.projects:
                                st.markdown(f"- 🚀 {proj}")
                        else:
                            st.info("No specific projects section parsed.")

                    with t_text:
                        st.text_area("Extracted Resume Text (PyMuPDF)", candidate.raw_text, height=350)
        else:
            st.info("No candidates match the specified filter criteria.")


# ==========================================
# VIEW: 💼 JOB DESCRIPTION MANAGER
# ==========================================
elif st.session_state.active_nav == "💼 Job Description":
    st.markdown(
        """
        <div class="recruiter-header">
            <h1>Job Requisition Manager</h1>
            <p>Customize the target job description, required technical skills, preferred skills, and minimum experience criteria.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Job Template Selector
    st.markdown("#### 📂 Load Pre-Configured Job Template")
    tpl_titles = [tpl["title"] for tpl in st.session_state.job_templates]
    selected_tpl_title = st.selectbox(
        "Choose a Template",
        options=["-- Custom Requisition --"] + tpl_titles
    )

    if st.button("Apply Selected Template"):
        tpl = next((t for t in st.session_state.job_templates if t["title"] == selected_tpl_title), None)
        if tpl:
            st.session_state.current_job = JobDescription(
                id=tpl["id"],
                title=tpl["title"],
                description=tpl["description"],
                required_skills=tpl["required_skills"],
                preferred_skills=tpl.get("preferred_skills", []),
                min_experience_years=float(tpl.get("min_experience_years", 3.0)),
                seniority_level=tpl.get("seniority_level", "Mid-Level")
            )
            st.success(f"Applied template: '{tpl['title']}'!")
            st.rerun()

    st.markdown("---")
    st.markdown("#### ✏️ Edit Active Job Requisition")

    with st.form("job_edit_form"):
        f_title = st.text_input("Job Title", value=st.session_state.current_job.title)
        
        c_sen, c_exp = st.columns(2)
        with c_sen:
            f_seniority = st.selectbox(
                "Seniority Level",
                options=["Entry-Level", "Mid-Level", "Senior", "Lead / Staff", "Principal / Director"],
                index=["Entry-Level", "Mid-Level", "Senior", "Lead / Staff", "Principal / Director"].index(
                    st.session_state.current_job.seniority_level if st.session_state.current_job.seniority_level in ["Entry-Level", "Mid-Level", "Senior", "Lead / Staff", "Principal / Director"] else "Mid-Level"
                )
            )
        with c_exp:
            f_min_exp = st.number_input(
                "Minimum Experience Required (Years)",
                min_value=0.0,
                max_value=25.0,
                value=float(st.session_state.current_job.min_experience_years),
                step=0.5
            )

        f_desc = st.text_area("Full Job Description", value=st.session_state.current_job.description, height=200)

        # Skills Taxonomy Options
        all_tax_skills = sorted(list(set(s for cat in SKILLS_TAXONOMY.values() for s in cat)))

        f_req_skills = st.multiselect(
            "Required Skills (Must Have - 45-60% Scoring Weight)",
            options=all_tax_skills + [s for s in st.session_state.current_job.required_skills if s not in all_tax_skills],
            default=st.session_state.current_job.required_skills
        )

        f_pref_skills = st.multiselect(
            "Preferred Skills (Nice to Have - 15% Scoring Weight)",
            options=all_tax_skills + [s for s in st.session_state.current_job.preferred_skills if s not in all_tax_skills],
            default=st.session_state.current_job.preferred_skills
        )

        submitted = st.form_submit_button("💾 Save & Update Job Criteria", type="primary")

        if submitted:
            is_valid, errors = JobValidator.validate_job_input(f_title, f_desc, f_req_skills)
            if not is_valid:
                for err in errors:
                    st.error(err)
            else:
                parser = JobParser()
                updated_job = parser.parse_job(
                    title=f_title,
                    description=f_desc,
                    required_skills=f_req_skills,
                    preferred_skills=f_pref_skills,
                    min_experience_years=f_min_exp,
                    seniority_level=f_seniority
                )
                st.session_state.current_job = updated_job
                st.success("✅ Job Requisition updated successfully! Candidate match scores have been recalculated.")
                st.rerun()

    # Auto Skill Extraction Helper
    st.markdown("---")
    st.markdown("#### ⚡ Auto-Extract Skills from Description")
    st.caption("Paste any raw job description to automatically identify required and preferred technical skills.")
    if st.button("🤖 Auto-Extract Skills from Current Description"):
        parser = JobParser()
        auto_req, auto_pref = parser._auto_extract_skills_from_jd(st.session_state.current_job.description)
        auto_exp = parser._detect_experience_requirement(st.session_state.current_job.description)
        
        st.session_state.current_job.required_skills = auto_req or st.session_state.current_job.required_skills
        st.session_state.current_job.preferred_skills = auto_pref or st.session_state.current_job.preferred_skills
        if auto_exp > 0:
            st.session_state.current_job.min_experience_years = auto_exp
            
        st.success(f"Extracted {len(auto_req)} required skills, {len(auto_pref)} preferred skills, and {auto_exp} yrs experience!")
        st.rerun()


# ==========================================
# VIEW: 📈 REPORTS & COMPARISON MATRIX
# ==========================================
elif st.session_state.active_nav == "📈 Reports & Compare":
    st.markdown(
        """
        <div class="recruiter-header">
            <h1>Recruitment Reports & Candidate Comparison</h1>
            <p>Compare top candidates head-to-head and export comprehensive evaluation reports in CSV and JSON formats.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    match_results = evaluate_candidates()
    ranked = CandidateRanker.rank_candidates(match_results)

    if not ranked:
        st.warning("⚠️ No candidate data available for reports. Please upload resumes in **⚡ Resume Screening**.")
    else:
        tab_compare, tab_export = st.tabs(["⚖️ Head-to-Head Candidate Comparison", "📥 Export Evaluation Reports"])

        # Tab 1: Comparison Matrix
        with tab_compare:
            st.markdown("### ⚖️ Side-by-Side Candidate Comparison Matrix")
            st.caption("Select 2 to 3 candidates to compare their skills, experience, and score metrics directly.")

            cand_options = {r["candidate_id"]: f"#{r['rank']} {r['candidate_name']} ({r['overall_score']}%)" for r in ranked}
            default_selection = list(cand_options.keys())[:min(3, len(cand_options))]

            selected_compare_ids = st.multiselect(
                "Select Candidates to Compare",
                options=list(cand_options.keys()),
                default=default_selection,
                format_func=lambda cid: cand_options[cid],
                max_selections=3
            )

            if len(selected_compare_ids) < 2:
                st.info("Please select at least 2 candidates to view side-by-side comparison.")
            else:
                cols = st.columns(len(selected_compare_ids))
                for idx, cid in enumerate(selected_compare_ids):
                    c_cand = st.session_state.candidates[cid]
                    c_res = next((r for r in match_results if r.candidate_id == cid), None)

                    with cols[idx]:
                        st.markdown(
                            f"""
                            <div class="candidate-card" style="text-align: center;">
                                <div style="font-size: 1.2rem; font-weight: 700;">{c_cand.name}</div>
                                <div style="font-size: 2rem; font-weight: 800; color: #2563EB; margin: 6px 0;">{c_res.overall_score}%</div>
                                <div>{get_badge_html(c_res.category)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        st.markdown(f"**Email:** `{c_cand.email or 'N/A'}`")
                        st.markdown(f"**Phone:** `{c_cand.phone or 'N/A'}`")
                        st.markdown(f"**Experience:** `{c_cand.total_experience_years} Years`")
                        
                        st.markdown("---")
                        st.markdown(f"**🛠️ Skills Score:** `{c_res.skills_score}/60.0`")
                        st.markdown(f"**⏳ Exp Score:** `{c_res.experience_score}/20.0`")
                        st.markdown(f"**🧠 Sim Score:** `{c_res.similarity_score}/20.0`")

                        st.markdown("---")
                        st.markdown(f"**🟢 Matching Required ({len(c_res.matching_required_skills)}):**")
                        st.markdown(render_skill_chips(c_res.matching_required_skills, "matched"), unsafe_allow_html=True)

                        st.markdown(f"**🔴 Missing Required ({len(c_res.missing_required_skills)}):**")
                        st.markdown(render_skill_chips(c_res.missing_required_skills, "missing"), unsafe_allow_html=True)

                        if c_cand.education:
                            st.markdown("---")
                            st.markdown("**🎓 Education:**")
                            for edu in c_cand.education:
                                st.caption(f"{edu.degree} - {edu.institution}")

        # Tab 2: Export Data
        with tab_export:
            st.markdown("### 📥 Export Recruitment Data")
            st.caption("Download standardized candidate reports ready for ATS upload, HR spreadsheets, or hiring manager review.")

            exp_c1, exp_c2 = st.columns(2)

            with exp_c1:
                st.markdown("#### 📊 Candidate Ranking Report (CSV)")
                st.write("Export all candidate scores, contact information, matched skills, missing skills, and evaluation takeaways.")
                
                csv_data = DataExporter.export_to_csv(
                    ranked_results=ranked,
                    candidate_profiles=st.session_state.candidates
                )

                st.download_button(
                    label="⬇️ Download Candidates CSV",
                    data=csv_data,
                    file_name=f"candidates_{st.session_state.current_job.id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )

            with exp_c2:
                st.markdown("#### 🔗 ATS Structured Payload (JSON)")
                st.write("Export structured JSON payload including job metadata and candidate analysis objects.")
                
                json_data = DataExporter.export_to_json(
                    ranked_results=ranked,
                    job=st.session_state.current_job
                )

                st.download_button(
                    label="⬇️ Download ATS Payload (JSON)",
                    data=json_data,
                    file_name=f"recruiter_payload_{st.session_state.current_job.id}.json",
                    mime="application/json",
                    use_container_width=True
                )

            st.markdown("---")
            st.markdown("#### 📄 Individual Candidate Evaluation Card (Markdown)")
            sel_report_id = st.selectbox(
                "Choose Candidate for Evaluation Report Card",
                options=[r["candidate_id"] for r in ranked],
                format_func=lambda cid: next(r["candidate_name"] for r in ranked if r["candidate_id"] == cid)
            )

            if sel_report_id:
                cand_obj = st.session_state.candidates[sel_report_id]
                match_obj = next(r for r in match_results if r.candidate_id == sel_report_id)
                report_md = DataExporter.generate_candidate_report(cand_obj, match_obj, st.session_state.current_job)
                
                st.download_button(
                    label=f"⬇️ Download {cand_obj.name}'s Report (.md)",
                    data=report_md,
                    file_name=f"Candidate_Report_{cand_obj.name.replace(' ', '_')}.md",
                    mime="text/markdown"
                )

                with st.expander("👁️ Preview Report Card", expanded=False):
                    st.markdown(report_md)
