"""Candidate Ranking, filtering, and aggregate recruitment analytics service."""
import logging
from typing import List, Dict, Any, Optional, Tuple

from models.candidate import CandidateProfile
from models.job import MatchResult, JobDescription

logger = logging.getLogger("ai_recruiter.ranking")


class CandidateRanker:
    """Handles sorting, filtering, and metric aggregation for candidate pools."""

    @staticmethod
    def rank_candidates(results: List[MatchResult]) -> List[Dict[str, Any]]:
        """
        Ranks candidates descending by overall score, then skills score, then experience.
        Returns a list of dicts with rank numbers attached.
        """
        if not results:
            return []

        sorted_results = sorted(
            results,
            key=lambda r: (r.overall_score, r.skills_score, r.candidate_experience_years),
            reverse=True
        )

        ranked = []
        for i, res in enumerate(sorted_results, start=1):
            item = res.to_dict()
            item["rank"] = i
            ranked.append(item)

        return ranked

    @staticmethod
    def filter_candidates(
        results: List[MatchResult],
        query: str = "",
        categories: Optional[List[str]] = None,
        min_score: float = 0.0,
        required_skill_filter: Optional[List[str]] = None,
        candidate_profiles: Optional[Dict[str, CandidateProfile]] = None
    ) -> List[MatchResult]:
        """Filters match results according to recruiter criteria."""
        filtered = results

        # 1. Search Query (Name or Email)
        if query and query.strip():
            q = query.strip().lower()
            filtered = [
                r for r in filtered
                if q in r.candidate_name.lower() or q in r.email.lower()
            ]

        # 2. Category Filter
        if categories:
            allowed = set(categories)
            filtered = [r for r in filtered if r.category in allowed]

        # 3. Minimum Score Filter
        if min_score > 0.0:
            filtered = [r for r in filtered if r.overall_score >= min_score]

        # 4. Specific Skill Filter
        if required_skill_filter and candidate_profiles:
            req_set = {s.lower() for s in required_skill_filter}
            matched_subset = []
            for r in filtered:
                cand = candidate_profiles.get(r.candidate_id)
                if cand:
                    cand_skills = {s.lower() for s in cand.all_skills}
                    if req_set.issubset(cand_skills):
                        matched_subset.append(r)
            filtered = matched_subset

        return filtered

    @staticmethod
    def calculate_dashboard_metrics(
        results: List[MatchResult],
        job: Optional[JobDescription] = None
    ) -> Dict[str, Any]:
        """Computes executive recruitment metrics and analytics."""
        total_resumes = len(results)
        if total_resumes == 0:
            return {
                "total_resumes": 0,
                "suitable_candidates": 0,
                "suitable_percentage": 0.0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "category_counts": {
                    "Excellent Match": 0,
                    "Good Match": 0,
                    "Moderate Match": 0,
                    "Low Match": 0
                },
                "top_matching_skills": [],
                "top_missing_skills": []
            }

        scores = [r.overall_score for r in results]
        suitable = [r for r in results if r.category in ["Excellent Match", "Good Match"]]
        
        category_counts = {
            "Excellent Match": sum(1 for r in results if r.category == "Excellent Match"),
            "Good Match": sum(1 for r in results if r.category == "Good Match"),
            "Moderate Match": sum(1 for r in results if r.category == "Moderate Match"),
            "Low Match": sum(1 for r in results if r.category == "Low Match")
        }

        # Skill frequency aggregations
        matching_skills_freq: Dict[str, int] = {}
        missing_skills_freq: Dict[str, int] = {}

        for r in results:
            for s in r.matching_required_skills + r.matching_preferred_skills:
                matching_skills_freq[s] = matching_skills_freq.get(s, 0) + 1
            for s in r.missing_required_skills:
                missing_skills_freq[s] = missing_skills_freq.get(s, 0) + 1

        top_matching = sorted(matching_skills_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        top_missing = sorted(missing_skills_freq.items(), key=lambda x: x[1], reverse=True)[:8]

        return {
            "total_resumes": total_resumes,
            "suitable_candidates": len(suitable),
            "suitable_percentage": round((len(suitable) / total_resumes) * 100.0, 1),
            "average_score": round(sum(scores) / total_resumes, 1),
            "highest_score": round(max(scores), 1),
            "lowest_score": round(min(scores), 1),
            "category_counts": category_counts,
            "top_matching_skills": top_matching,
            "top_missing_skills": top_missing
        }
