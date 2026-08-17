"""Job description and matching evaluation data models."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class JobDescription:
    """Represents a target job requisition."""
    id: str = "default_job"
    title: str = "Software Engineer"
    description: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    min_experience_years: float = 0.0
    seniority_level: str = "Mid-Level"
    education_requirement: str = "Bachelor's Degree in Computer Science or related field"
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "min_experience_years": self.min_experience_years,
            "seniority_level": self.seniority_level,
            "education_requirement": self.education_requirement,
            "keywords": self.keywords,
        }


@dataclass
class MatchResult:
    """Detailed candidate-to-job matching evaluation."""
    candidate_id: str
    candidate_name: str
    email: str
    phone: str
    overall_score: float
    category: str
    skills_score: float
    experience_score: float
    similarity_score: float
    matching_required_skills: List[str] = field(default_factory=list)
    missing_required_skills: List[str] = field(default_factory=list)
    matching_preferred_skills: List[str] = field(default_factory=list)
    missing_preferred_skills: List[str] = field(default_factory=list)
    additional_skills: List[str] = field(default_factory=list)
    candidate_experience_years: float = 0.0
    required_experience_years: float = 0.0
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    detailed_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "email": self.email,
            "phone": self.phone,
            "overall_score": self.overall_score,
            "category": self.category,
            "skills_score": self.skills_score,
            "experience_score": self.experience_score,
            "similarity_score": self.similarity_score,
            "matching_required_skills": self.matching_required_skills,
            "missing_required_skills": self.missing_required_skills,
            "matching_preferred_skills": self.matching_preferred_skills,
            "missing_preferred_skills": self.missing_preferred_skills,
            "additional_skills": self.additional_skills,
            "candidate_experience_years": self.candidate_experience_years,
            "required_experience_years": self.required_experience_years,
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "detailed_summary": self.detailed_summary,
        }
