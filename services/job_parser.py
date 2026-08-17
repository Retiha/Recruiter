"""Job Description parser and requirement normalizer."""
import logging
import re
from typing import List, Dict, Set, Optional, Tuple

from models.job import JobDescription
from models.nlp_model import get_nlp_engine
from services.resume_parser import SKILLS_TAXONOMY, SKILL_SYNONYMS

logger = logging.getLogger("ai_recruiter.job_parser")


class JobParser:
    """Parses and normalizes job requirements, skills, and experience criteria."""

    def __init__(self):
        self.nlp = get_nlp_engine()

    def parse_job(
        self,
        title: str,
        description: str,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        min_experience_years: float = 0.0,
        seniority_level: str = "Mid-Level",
        job_id: str = "job_default"
    ) -> JobDescription:
        """
        Creates a structured JobDescription, auto-extracting missing elements from description if needed.
        """
        raw_text = f"{title}\n{description}"
        
        # Normalize explicit skills
        normalized_req = self._normalize_skills_list(required_skills or [])
        normalized_pref = self._normalize_skills_list(preferred_skills or [])

        # Auto-extract skills if user didn't enter any
        if not normalized_req:
            auto_req, auto_pref = self._auto_extract_skills_from_jd(description)
            normalized_req = auto_req
            if not normalized_pref:
                normalized_pref = auto_pref

        # Auto-detect experience if set to 0 and mentioned in text
        if min_experience_years <= 0:
            detected_exp = self._detect_experience_requirement(raw_text)
            if detected_exp > 0:
                min_experience_years = detected_exp

        # Extract dominant keywords from job text
        keywords = self.nlp.extract_keywords(raw_text, top_n=15)

        return JobDescription(
            id=job_id,
            title=title.strip() or "Software Engineer",
            description=description.strip(),
            required_skills=normalized_req,
            preferred_skills=normalized_pref,
            min_experience_years=float(min_experience_years),
            seniority_level=seniority_level,
            keywords=keywords
        )

    def _normalize_skills_list(self, skills: List[str]) -> List[str]:
        """Cleans and standardizes skill names."""
        result = []
        for s in skills:
            clean = s.strip()
            if clean:
                canonical = SKILL_SYNONYMS.get(clean.lower(), clean)
                result.append(canonical)
        return list(dict.fromkeys(result))

    def _auto_extract_skills_from_jd(self, jd_text: str) -> Tuple[List[str], List[str]]:
        """Scans job description text to auto-identify required vs preferred skills."""
        if not jd_text or not jd_text.strip():
            return [], []

        jd_lower = jd_text.lower()
        required: List[str] = []
        preferred: List[str] = []

        # Split into required section vs preferred section if marked
        req_pattern = re.compile(r'(?:requirements|qualifications|must\s+have|required\s+skills|what\s+you(?:\'ll)?\s+need)\b', re.IGNORECASE)
        pref_pattern = re.compile(r'(?:preferred|nice\s+to\s+have|bonus|plus|desired|optional)\b', re.IGNORECASE)

        is_in_preferred = False
        lines = jd_text.split("\n")

        for line in lines:
            line_lower = line.lower()
            if pref_pattern.search(line_lower):
                is_in_preferred = True
            elif req_pattern.search(line_lower):
                is_in_preferred = False

            # Extract matching skills on this line
            for cat, skill_list in SKILLS_TAXONOMY.items():
                for skill in skill_list:
                    escaped = re.escape(skill.lower())
                    if len(skill) == 1:
                        pattern = rf'(?<![a-zA-Z0-9+#])\b{escaped}\b(?![a-zA-Z0-9+#])'
                    elif skill.endswith("+") or skill.endswith("#") or skill.startswith("."):
                        pattern = rf'(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])'
                    else:
                        pattern = rf'\b{escaped}\b'

                    if re.search(pattern, line_lower):
                        canonical = SKILL_SYNONYMS.get(skill.lower(), skill)
                        if is_in_preferred:
                            preferred.append(canonical)
                        else:
                            required.append(canonical)

        # De-duplicate
        req_clean = list(dict.fromkeys(required))
        pref_clean = [p for p in list(dict.fromkeys(preferred)) if p not in req_clean]
        
        return req_clean, pref_clean

    def _detect_experience_requirement(self, text: str) -> float:
        """Extracts minimum required years from JD."""
        patterns = [
            r'(\d+)\+?\s*(?:to\s*\d+)?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:relevant|work|professional)?\s*experience',
            r'(?:at\s+least|minimum\s+of)\s*(\d+)\s*(?:years?|yrs?)',
            r'(\d+)\s*(?:years?|yrs?)\s*minimum'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return 0.0
