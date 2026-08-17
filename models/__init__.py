"""Data models and NLP engine package for AI Recruiter."""
from .candidate import CandidateProfile, EducationEntry, ExperienceEntry
from .job import JobDescription, MatchResult

__all__ = [
    "CandidateProfile",
    "EducationEntry",
    "ExperienceEntry",
    "JobDescription",
    "MatchResult",
]
