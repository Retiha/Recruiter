"""Candidate profile and sub-entity data models."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class EducationEntry:
    """Represents an education entry from a resume."""
    degree: str = ""
    institution: str = ""
    year: str = ""
    field_of_study: str = ""
    details: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "degree": self.degree,
            "institution": self.institution,
            "year": self.year,
            "field_of_study": self.field_of_study,
            "details": self.details,
        }


@dataclass
class ExperienceEntry:
    """Represents a work experience entry from a resume."""
    title: str = ""
    company: str = ""
    date_range: str = ""
    duration_years: float = 0.0
    description: str = ""
    highlights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "date_range": self.date_range,
            "duration_years": self.duration_years,
            "description": self.description,
            "highlights": self.highlights,
        }


@dataclass
class CandidateProfile:
    """Comprehensive candidate profile extracted from a resume."""
    id: str
    file_name: str
    name: str = "Unknown Candidate"
    email: str = ""
    phone: str = ""
    links: Dict[str, str] = field(default_factory=dict)
    location: str = ""
    summary: str = ""
    total_experience_years: float = 0.0
    skills_by_category: Dict[str, List[str]] = field(default_factory=dict)
    all_skills: List[str] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    experience: List[ExperienceEntry] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    raw_text: str = ""
    file_size_kb: float = 0.0
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "links": self.links,
            "location": self.location,
            "summary": self.summary,
            "total_experience_years": self.total_experience_years,
            "skills_by_category": self.skills_by_category,
            "all_skills": self.all_skills,
            "education": [e.to_dict() for e in self.education],
            "experience": [e.to_dict() for e in self.experience],
            "projects": self.projects,
            "certifications": self.certifications,
            "file_size_kb": self.file_size_kb,
            "keywords": self.keywords,
        }
