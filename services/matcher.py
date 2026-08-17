"""Candidate-to-Job Matching Engine using a transparent 60/20/20 rule-based scoring system."""
import logging
import re
from typing import List, Dict, Set, Tuple, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.candidate import CandidateProfile
from models.job import JobDescription, MatchResult

logger = logging.getLogger("ai_recruiter.matcher")


class CandidateJobMatcher:
    """
    Transparent rule-based scoring engine for candidate-job matching.
    
    Weights:
      - Skills match: 60% (Required Skills: up to 45-60%, Preferred Skills: up to 15%)
      - Experience relevance: 20%
      - Job-description keyword/semantic similarity: 20%
    """

    @classmethod
    def match(cls, candidate: CandidateProfile, job: JobDescription) -> MatchResult:
        """Evaluates a single candidate profile against a job description."""
        
        # 1. Skills Matching (60% weight)
        skills_score, match_req, miss_req, match_pref, miss_pref, add_skills = cls._calculate_skills_score(
            candidate_skills=candidate.all_skills,
            required_skills=job.required_skills,
            preferred_skills=job.preferred_skills
        )

        # 2. Experience Relevance (20% weight)
        exp_score, exp_details = cls._calculate_experience_score(
            candidate_exp=candidate.total_experience_years,
            required_exp=job.min_experience_years
        )

        # 3. Context & Keyword Similarity (20% weight)
        sim_score, sim_pct = cls._calculate_similarity_score(
            candidate_text=f"{candidate.name} {candidate.summary} {' '.join(candidate.all_skills)} {candidate.raw_text}",
            job_text=f"{job.title} {job.description} {' '.join(job.required_skills)} {' '.join(job.preferred_skills)}"
        )

        # 4. Total Combined Score (0.0 to 100.0)
        overall_score = round(skills_score + exp_score + sim_score, 1)
        overall_score = min(max(overall_score, 0.0), 100.0)

        # 5. Categorize
        category = cls._categorize_score(overall_score)

        # 6. Strengths & Improvement Areas
        strengths, improvements = cls._generate_feedback(
            overall_score=overall_score,
            match_req=match_req,
            miss_req=miss_req,
            match_pref=match_pref,
            miss_pref=miss_pref,
            candidate_exp=candidate.total_experience_years,
            required_exp=job.min_experience_years,
            sim_pct=sim_pct
        )

        # 7. Detailed Summary Narrative
        summary = cls._generate_narrative(
            candidate_name=candidate.name,
            overall_score=overall_score,
            category=category,
            skills_score=skills_score,
            exp_score=exp_score,
            sim_score=sim_score,
            match_req_count=len(match_req),
            total_req_count=len(job.required_skills),
            candidate_exp=candidate.total_experience_years,
            required_exp=job.min_experience_years
        )

        return MatchResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            overall_score=overall_score,
            category=category,
            skills_score=round(skills_score, 1),
            experience_score=round(exp_score, 1),
            similarity_score=round(sim_score, 1),
            matching_required_skills=match_req,
            missing_required_skills=miss_req,
            matching_preferred_skills=match_pref,
            missing_preferred_skills=miss_pref,
            additional_skills=add_skills,
            candidate_experience_years=candidate.total_experience_years,
            required_experience_years=job.min_experience_years,
            strengths=strengths,
            improvement_areas=improvements,
            detailed_summary=summary
        )

    @classmethod
    def match_all(cls, candidates: List[CandidateProfile], job: JobDescription) -> List[MatchResult]:
        """Evaluates multiple candidates against a target job."""
        return [cls.match(cand, job) for cand in candidates]

    @staticmethod
    def _calculate_skills_score(
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Tuple[float, List[str], List[str], List[str], List[str], List[str]]:
        """Calculates skills match score out of 60 maximum points."""
        cand_skills_lower = {s.lower(): s for s in candidate_skills}

        def check_skill_match(target_skill: str) -> bool:
            t_lower = target_skill.lower()
            if t_lower in cand_skills_lower:
                return True
            # Also check substring match or aliases
            for cs in cand_skills_lower:
                if t_lower == cs or (len(t_lower) > 3 and t_lower in cs) or (len(cs) > 3 and cs in t_lower):
                    return True
            return False

        # Required skills
        match_req = [s for s in required_skills if check_skill_match(s)]
        miss_req = [s for s in required_skills if not check_skill_match(s)]

        # Preferred skills
        match_pref = [s for s in preferred_skills if check_skill_match(s)]
        miss_pref = [s for s in preferred_skills if not check_skill_match(s)]

        # Additional candidate skills
        all_job_skills_lower = {s.lower() for s in (required_skills + preferred_skills)}
        add_skills = [s for s in candidate_skills if s.lower() not in all_job_skills_lower]

        # Scoring allocation
        if not required_skills and not preferred_skills:
            # No skills requested in JD
            return 60.0, match_req, miss_req, match_pref, miss_pref, add_skills

        if not preferred_skills:
            # 60 points solely based on required skills
            ratio = len(match_req) / len(required_skills) if required_skills else 1.0
            score = ratio * 60.0
        elif not required_skills:
            # 60 points solely based on preferred skills
            ratio = len(match_pref) / len(preferred_skills) if preferred_skills else 1.0
            score = ratio * 60.0
        else:
            # 45 points for required + 15 points for preferred
            req_ratio = len(match_req) / len(required_skills)
            pref_ratio = len(match_pref) / len(preferred_skills)
            score = (req_ratio * 45.0) + (pref_ratio * 15.0)

        return min(max(score, 0.0), 60.0), match_req, miss_req, match_pref, miss_pref, add_skills

    @staticmethod
    def _calculate_experience_score(candidate_exp: float, required_exp: float) -> Tuple[float, str]:
        """Calculates experience score out of 20 maximum points."""
        if required_exp <= 0.0:
            return 20.0, f"Candidate has {candidate_exp} yrs experience (no minimum requirement specified)."

        if candidate_exp >= required_exp:
            surplus = round(candidate_exp - required_exp, 1)
            details = f"Exceeds requirement: {candidate_exp} yrs vs {required_exp} yrs required (+{surplus} yrs)."
            return 20.0, details

        # Proportional score
        ratio = max(candidate_exp / required_exp, 0.0)
        score = round(ratio * 20.0, 1)
        gap = round(required_exp - candidate_exp, 1)
        details = f"Below requirement: {candidate_exp} yrs vs {required_exp} yrs required (-{gap} yrs)."
        return min(max(score, 0.0), 20.0), details

    @staticmethod
    def _calculate_similarity_score(candidate_text: str, job_text: str) -> Tuple[float, float]:
        """Calculates TF-IDF context cosine similarity out of 20 maximum points."""
        if not candidate_text.strip() or not job_text.strip():
            return 10.0, 50.0

        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=200
            )
            tfidf = vectorizer.fit_transform([candidate_text, job_text])
            sim = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
            # Cosine similarity is usually in range 0.1 - 0.7 for resume-JD pairs
            # Scale non-linearly to provide a realistic 0-20 score distribution
            scaled_sim = min(sim * 1.5, 1.0)
            score = round(scaled_sim * 20.0, 1)
            pct = round(scaled_sim * 100.0, 1)
            return score, pct
        except Exception:
            return 10.0, 50.0

    @staticmethod
    def _categorize_score(score: float) -> str:
        """Classifies the overall match percentage into categories."""
        if score >= 80.0:
            return "Excellent Match"
        elif score >= 65.0:
            return "Good Match"
        elif score >= 50.0:
            return "Moderate Match"
        else:
            return "Low Match"

    @staticmethod
    def _generate_feedback(
        overall_score: float,
        match_req: List[str],
        miss_req: List[str],
        match_pref: List[str],
        miss_pref: List[str],
        candidate_exp: float,
        required_exp: float,
        sim_pct: float
    ) -> Tuple[List[str], List[str]]:
        """Produces bullet-point strengths and areas of improvement."""
        strengths = []
        improvements = []

        # Skills feedback
        if match_req:
            strengths.append(f"Matches key required skills: {', '.join(match_req[:5])}.")
        if match_pref:
            strengths.append(f"Possesses preferred skillsets: {', '.join(match_pref[:4])}.")
        if miss_req:
            improvements.append(f"Missing required skills: {', '.join(miss_req[:5])}.")
        if miss_pref and len(miss_req) == 0:
            improvements.append(f"Missing bonus preferred skills: {', '.join(miss_pref[:3])}.")

        # Experience feedback
        if required_exp > 0:
            if candidate_exp >= required_exp:
                strengths.append(f"Meets experience criteria ({candidate_exp} yrs vs {required_exp} yrs target).")
            else:
                improvements.append(f"Experience gap: has {candidate_exp} yrs vs {required_exp} yrs target.")
        elif candidate_exp > 0:
            strengths.append(f"Brings {candidate_exp} years of relevant professional background.")

        # Similarity feedback
        if sim_pct >= 60.0:
            strengths.append("High contextual and vocabulary alignment with job description.")
        elif sim_pct < 35.0:
            improvements.append("Low overall domain keyword overlap with job requirements.")

        if not strengths:
            strengths.append("General technical background noted in resume.")
        if not improvements:
            improvements.append("Candidate strongly meets all stated technical and experience criteria.")

        return strengths, improvements

    @staticmethod
    def _generate_narrative(
        candidate_name: str,
        overall_score: float,
        category: str,
        skills_score: float,
        exp_score: float,
        sim_score: float,
        match_req_count: int,
        total_req_count: int,
        candidate_exp: float,
        required_exp: float
    ) -> str:
        """Generates a concise recruiter-friendly evaluation narrative."""
        exp_str = f"{candidate_exp} yrs" if candidate_exp > 0 else "unspecified"
        req_str = f"out of {total_req_count} required skills" if total_req_count > 0 else "skills criteria"
        
        return (
            f"{candidate_name} scored {overall_score}% ({category}). "
            f"Skill Match: {skills_score}/60.0 ({match_req_count} {req_str} matched). "
            f"Experience: {exp_score}/20.0 ({exp_str} vs {required_exp} yrs required). "
            f"Context Relevance: {sim_score}/20.0."
        )
