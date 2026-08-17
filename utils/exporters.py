"""Data export utilities for generating CSV, JSON, and evaluation summaries."""
import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from models.candidate import CandidateProfile
from models.job import MatchResult, JobDescription


class DataExporter:
    """Handles candidate ranking and evaluation data exports."""

    @staticmethod
    def export_to_csv(
        ranked_results: List[Dict[str, Any]],
        candidate_profiles: Optional[Dict[str, CandidateProfile]] = None
    ) -> str:
        """
        Generates CSV text formatted for recruiters and HR analytics.
        """
        output = io.StringIO()
        fieldnames = [
            "Rank",
            "Candidate Name",
            "Email",
            "Phone",
            "Match Score (%)",
            "Match Category",
            "Skills Score (60 max)",
            "Experience Score (20 max)",
            "Similarity Score (20 max)",
            "Matching Skills",
            "Missing Skills",
            "Candidate Experience (Yrs)",
            "Required Experience (Yrs)",
            "Education",
            "Top Strengths",
            "Improvement Areas"
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()

        for item in ranked_results:
            cand_id = item.get("candidate_id", "")
            cand = candidate_profiles.get(cand_id) if candidate_profiles else None

            # Aggregate matching skills
            match_skills = item.get("matching_required_skills", []) + item.get("matching_preferred_skills", [])
            miss_skills = item.get("missing_required_skills", []) + item.get("missing_preferred_skills", [])

            edu_summary = ""
            if cand and cand.education:
                edu_summary = "; ".join([f"{e.degree} ({e.institution})" for e in cand.education if e.degree])

            row = {
                "Rank": item.get("rank", ""),
                "Candidate Name": item.get("candidate_name", ""),
                "Email": item.get("email", ""),
                "Phone": item.get("phone", ""),
                "Match Score (%)": item.get("overall_score", 0.0),
                "Match Category": item.get("category", ""),
                "Skills Score (60 max)": item.get("skills_score", 0.0),
                "Experience Score (20 max)": item.get("experience_score", 0.0),
                "Similarity Score (20 max)": item.get("similarity_score", 0.0),
                "Matching Skills": ", ".join(match_skills),
                "Missing Skills": ", ".join(miss_skills),
                "Candidate Experience (Yrs)": item.get("candidate_experience_years", 0.0),
                "Required Experience (Yrs)": item.get("required_experience_years", 0.0),
                "Education": edu_summary,
                "Top Strengths": " | ".join(item.get("strengths", [])),
                "Improvement Areas": " | ".join(item.get("improvement_areas", []))
            }
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def export_to_json(
        ranked_results: List[Dict[str, Any]],
        job: Optional[JobDescription] = None
    ) -> str:
        """
        Generates a comprehensive structured JSON payload for ATS integration.
        """
        payload = {
            "exported_at": datetime.now().isoformat(),
            "job_profile": job.to_dict() if job else None,
            "total_candidates": len(ranked_results),
            "candidates": ranked_results
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def generate_candidate_report(
        candidate: CandidateProfile,
        match_result: MatchResult,
        job: JobDescription
    ) -> str:
        """Generates a detailed Markdown evaluation card for a candidate."""
        all_matched = match_result.matching_required_skills + match_result.matching_preferred_skills
        all_missed = match_result.missing_required_skills + match_result.missing_preferred_skills

        lines = [
            f"# Candidate Evaluation Report: {candidate.name}",
            f"**Target Role:** {job.title} | **Date:** {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## 🎯 Match Summary",
            f"- **Overall Match Score:** {match_result.overall_score}% ({match_result.category})",
            f"- **Skills Match:** {match_result.skills_score} / 60.0",
            f"- **Experience Relevance:** {match_result.experience_score} / 20.0 ({candidate.total_experience_years} yrs vs {job.min_experience_years} yrs required)",
            f"- **Context Alignment:** {match_result.similarity_score} / 20.0",
            "",
            "## 👤 Candidate Contact",
            f"- **Email:** {candidate.email or 'N/A'}",
            f"- **Phone:** {candidate.phone or 'N/A'}",
            f"- **LinkedIn:** {candidate.links.get('linkedin', 'N/A')}",
            f"- **GitHub:** {candidate.links.get('github', 'N/A')}",
            "",
            "## 🛠️ Skills Analysis",
            f"- **Matching Skills ({len(all_matched)}):** {', '.join(all_matched) if all_matched else 'None'}",
            f"- **Missing Skills ({len(all_missed)}):** {', '.join(all_missed) if all_missed else 'None'}",
            f"- **Additional Candidate Skills:** {', '.join(match_result.additional_skills[:10]) if match_result.additional_skills else 'None'}",
            "",
            "## 💡 Key Strengths",
        ]

        for st in match_result.strengths:
            lines.append(f"- {st}")

        lines.append("")
        lines.append("## ⚠️ Areas for Review / Upskilling")
        for imp in match_result.improvement_areas:
            lines.append(f"- {imp}")

        if candidate.education:
            lines.append("")
            lines.append("## 🎓 Education")
            for edu in candidate.education:
                lines.append(f"- **{edu.degree}** - {edu.institution} ({edu.year})")

        return "\n".join(lines)
