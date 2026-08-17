"""Resume Parsing Service extracting candidate info, contact details, skills, experience, and education."""
import logging
import re
import uuid
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional, Any

from models.candidate import CandidateProfile, EducationEntry, ExperienceEntry
from models.nlp_model import (
    get_nlp_engine,
    EMAIL_REGEX,
    PHONE_REGEX,
    LINKEDIN_REGEX,
    GITHUB_REGEX,
    URL_REGEX,
)

logger = logging.getLogger("ai_recruiter.resume_parser")

# Comprehensive Curated Technical Skills Taxonomy
SKILLS_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go", "Golang", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Dart", "SQL", "HTML5", "CSS3",
        "Bash", "Shell", "PowerShell", "Perl", "Haskell", "Elixir", "Clojure", "MATLAB", "VBA"
    ],
    "Frameworks & Libraries": [
        "React", "React.js", "React Native", "Angular", "Vue.js", "Vue", "Next.js", "Nuxt.js",
        "Node.js", "Express.js", "Express", "NestJS", "FastAPI", "Django", "Flask", "Spring Boot",
        "Spring", ".NET", ".NET Core", "ASP.NET", "Ruby on Rails", "Laravel", "PyTorch", "TensorFlow",
        "Keras", "Scikit-Learn", "Pandas", "NumPy", "Tailwind CSS", "Bootstrap", "Redux", "GraphQL",
        "REST API", "RESTful APIs", "gRPC", "jQuery", "Sass", "LESS", "Streamlit", "Gradio"
    ],
    "Cloud & DevOps": [
        "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud", "Google Cloud Platform",
        "Docker", "Kubernetes", "K8s", "Terraform", "Ansible", "Jenkins", "CI/CD", "GitHub Actions",
        "GitLab CI", "Helm", "Prometheus", "Grafana", "Linux", "Unix", "Nginx", "Apache",
        "Serverless", "AWS Lambda", "CloudFormation", "OpenShift", "CircleCI", "ArgoCD"
    ],
    "Databases": [
        "PostgreSQL", "Postgres", "MySQL", "SQLite", "MongoDB", "Redis", "Cassandra", "DynamoDB",
        "Elasticsearch", "Oracle Database", "Oracle", "Microsoft SQL Server", "MS SQL", "Neo4j",
        "Couchbase", "Snowflake", "BigQuery", "Supabase", "Firebase", "Firestore", "MariaDB"
    ],
    "AI & Data Science": [
        "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing", "Computer Vision",
        "Large Language Models", "LLMs", "Generative AI", "RAG", "Data Analysis", "Data Engineering",
        "Data Science", "ETL", "Apache Spark", "Spark", "Kafka", "Apache Kafka", "Airflow",
        "Hugging Face", "LangChain", "LlamaIndex", "OpenCV", "Tableau", "Power BI", "Statistics"
    ],
    "Tools & Methodologies": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Agile", "Scrum",
        "Kanban", "Microservices", "System Design", "Unit Testing", "TDD", "Test-Driven Development",
        "Integration Testing", "Postman", "Swagger", "Figma", "Docker Compose", "Object-Oriented Programming",
        "OOP", "Design Patterns", "Clean Architecture", "Code Review"
    ]
}

# Skill synonyms & canonical mappings
SKILL_SYNONYMS: Dict[str, str] = {
    "golang": "Go",
    "react.js": "React",
    "reactjs": "React",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "spring": "Spring Boot",
    "k8s": "Kubernetes",
    "postgres": "PostgreSQL",
    "amazon web services": "AWS",
    "microsoft azure": "Azure",
    "google cloud platform": "Google Cloud",
    "gcp": "Google Cloud",
    "ms sql": "Microsoft SQL Server",
    "rest": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "spark": "Apache Spark",
    "kafka": "Apache Kafka",
    "tdd": "Test-Driven Development",
    "oop": "Object-Oriented Programming",
    "ci / cd": "CI/CD",
    "ci-cd": "CI/CD",
}

# Section Header Regular Expressions
SECTION_PATTERNS = {
    "experience": re.compile(
        r'^(?:work\s+experience|professional\s+experience|employment\s+history|experience|work\s+history|career\s+history)\b',
        re.IGNORECASE | re.MULTILINE
    ),
    "education": re.compile(
        r'^(?:education|academic\s+background|academic\s+qualifications|qualifications|academic\s+history)\b',
        re.IGNORECASE | re.MULTILINE
    ),
    "skills": re.compile(
        r'^(?:technical\s+skills|skills\s*(?:&|and)?\s*technologies|core\s+competencies|skills|technologies|expertise)\b',
        re.IGNORECASE | re.MULTILINE
    ),
    "projects": re.compile(
        r'^(?:projects|key\s+projects|personal\s+projects|academic\s+projects|technical\s+projects)\b',
        re.IGNORECASE | re.MULTILINE
    ),
    "certifications": re.compile(
        r'^(?:certifications|certificates|licenses\s*(?:&|and)?\s*certifications|professional\s+certifications)\b',
        re.IGNORECASE | re.MULTILINE
    ),
    "summary": re.compile(
        r'^(?:professional\s+summary|executive\s+summary|summary|profile|about\s+me|career\s+objective|objective)\b',
        re.IGNORECASE | re.MULTILINE
    )
}

DEGREE_PATTERNS = [
    (r'\b(?:ph\.?d|doctor\s+of\s+philosophy|doctorate)\b', "Ph.D."),
    (r'\b(?:m\.?s\.?|master\s+of\s+science|m\.?tech|m\.?e\.?|master\s+of\s+engineering|msc|masters?)\b', "Master's Degree"),
    (r'\b(?:m\.?b\.?a\.?|master\s+of\s+business\s+administration)\b', "MBA"),
    (r'\b(?:b\.?s\.?|bachelor\s+of\s+science|b\.?tech|b\.?e\.?|bachelor\s+of\s+engineering|bsc|bachelors?|b\.?a\.?)\b', "Bachelor's Degree"),
    (r'\b(?:associate\s+degree|associate\s+of\s+science|associate\s+of\s+arts)\b', "Associate Degree"),
]


class ResumeParser:
    """Extracts structured candidate information from resume text."""

    def __init__(self):
        self.nlp = get_nlp_engine()

    def parse(self, text: str, file_name: str = "resume.pdf", file_size_kb: float = 0.0) -> CandidateProfile:
        """
        Parses full resume text into a CandidateProfile model.
        """
        candidate_id = f"cand_{uuid.uuid4().hex[:8]}"
        if not text or not text.strip():
            return CandidateProfile(
                id=candidate_id,
                file_name=file_name,
                name="Unknown Candidate",
                file_size_kb=file_size_kb,
                raw_text=text or ""
            )

        # 1. Contact Information
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        links = self._extract_links(text)

        # 2. Candidate Name
        name = self._extract_name(text, email=email, file_name=file_name)

        # 3. Sections segmentation
        sections = self._split_sections(text)

        # 4. Skills extraction
        skills_by_cat, all_skills = self._extract_skills(text)

        # 5. Experience parsing & total years calculation
        exp_entries, total_years = self._extract_experience(sections.get("experience", text))
        
        # If total_years is 0, attempt global text date range scan
        if total_years == 0.0:
            total_years = self._calculate_years_from_text(text)

        # 6. Education parsing
        education_entries = self._extract_education(sections.get("education", text))

        # 7. Projects & Certifications
        projects = self._extract_projects(sections.get("projects", ""))
        certifications = self._extract_certifications(sections.get("certifications", text))

        # 8. Summary & Keywords
        summary = sections.get("summary", "")
        if not summary:
            # First few lines as brief summary
            lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
            summary = lines[0] if lines else ""

        keywords = self.nlp.extract_keywords(text, top_n=12)

        return CandidateProfile(
            id=candidate_id,
            file_name=file_name,
            name=name,
            email=email,
            phone=phone,
            links=links,
            summary=summary[:300] + ("..." if len(summary) > 300 else ""),
            total_experience_years=round(total_years, 1),
            skills_by_category=skills_by_cat,
            all_skills=all_skills,
            education=education_entries,
            experience=exp_entries,
            projects=projects,
            certifications=certifications,
            raw_text=text,
            file_size_kb=file_size_kb,
            keywords=keywords
        )

    def _extract_email(self, text: str) -> str:
        match = EMAIL_REGEX.search(text)
        return match.group(0).strip() if match else ""

    def _extract_phone(self, text: str) -> str:
        matches = PHONE_REGEX.findall(text)
        if matches:
            for m in matches:
                # If tuple from groups or string
                candidate = m if isinstance(m, str) else "".join(m)
                # Ensure minimum length of digits
                digits = re.sub(r'\D', '', candidate)
                if 7 <= len(digits) <= 15:
                    return candidate.strip()
            
            # Alternative direct search
            direct_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            if direct_match:
                return direct_match.group(0).strip()
        return ""

    def _extract_links(self, text: str) -> Dict[str, str]:
        links = {}
        li_match = LINKEDIN_REGEX.search(text)
        if li_match:
            links["linkedin"] = f"https://linkedin.com/in/{li_match.group(1)}"
        
        gh_match = GITHUB_REGEX.search(text)
        if gh_match:
            links["github"] = f"https://github.com/{gh_match.group(1)}"

        # Look for portfolio or personal websites
        urls = URL_REGEX.findall(text)
        for u in urls:
            if "linkedin.com" not in u and "github.com" not in u and "gitlab.com" not in u:
                links["portfolio"] = u
                break
        return links

    def _extract_name(self, text: str, email: str = "", file_name: str = "") -> str:
        """Extracts candidate name using NLP NER and layout heuristics."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        
        # Check first 6 lines
        candidate_lines = lines[:6]
        
        # Exclude common non-name headers
        ignore_words = {
            "resume", "curriculum", "vitae", "cv", "page", "contact", "email", "phone",
            "profile", "summary", "experience", "education", "skills", "github", "linkedin",
            "portfolio", "http", "https", "www", "com", "address", "developer", "engineer"
        }

        # Try spaCy NER on the top block
        if self.nlp.is_spacy_available and candidate_lines:
            top_block = "\n".join(candidate_lines)
            entities = self.nlp.extract_entities(top_block)
            for ent_text, label in entities:
                if label == "PERSON" and 2 <= len(ent_text.split()) <= 4:
                    cleaned_ent = re.sub(r'[^a-zA-Z\s\.\'-]', '', ent_text).strip()
                    if cleaned_ent and not any(w in cleaned_ent.lower().split() for w in ignore_words):
                        return cleaned_ent.title()

        # Heuristic: inspect top lines for capitalized name format
        for line in candidate_lines:
            # Skip lines with email, phone, links, or section keywords
            if "@" in line or any(char.isdigit() for char in line) or "http" in line.lower():
                continue
            
            cleaned = re.sub(r'[^a-zA-Z\s\.\'-]', '', line).strip()
            words = cleaned.split()
            if 2 <= len(words) <= 4:
                if not any(w.lower() in ignore_words for w in words):
                    # Looks like a genuine human name
                    return cleaned.title()

        # Fallback to filename if readable
        if file_name and file_name not in ["resume.pdf", "uploaded_resume.pdf"]:
            name_part = file_name.replace(".pdf", "").replace("_", " ").replace("-", " ")
            # Remove keywords like resume or cv
            name_part = re.sub(r'\b(resume|cv|profile|doc)\b', '', name_part, flags=re.IGNORECASE).strip()
            if 2 <= len(name_part.split()) <= 4:
                return name_part.title()

        # Fallback to email username if available
        if email and "@" in email:
            user_part = email.split("@")[0]
            clean_user = re.sub(r'[0-9._-]+', ' ', user_part).strip().title()
            if len(clean_user.split()) >= 2:
                return clean_user

        return candidate_lines[0].title() if candidate_lines else "Unknown Candidate"

    def _split_sections(self, text: str) -> Dict[str, str]:
        """Segments resume into major recognized sections."""
        lines = text.split("\n")
        sections: Dict[str, List[str]] = {
            "summary": [],
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "other": []
        }

        current_section = "other"
        
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            # Check if line matches a section header
            matched = False
            for sec_name, pattern in SECTION_PATTERNS.items():
                # Headers are usually short (< 50 chars)
                if len(trimmed) < 50 and pattern.search(trimmed):
                    current_section = sec_name
                    matched = True
                    break
            
            if not matched:
                sections[current_section].append(line)

        return {k: "\n".join(v).strip() for k, v in sections.items()}

    def _extract_skills(self, text: str) -> Tuple[Dict[str, List[str]], List[str]]:
        """Extracts technical skills organized by category using exact word boundaries."""
        categorized_skills: Dict[str, List[str]] = {}
        all_detected: Set[str] = set()

        text_lower = text.lower()

        for category, skill_list in SKILLS_TAXONOMY.items():
            cat_matched = []
            for skill in skill_list:
                # Skill regex with careful word boundaries
                # Handle special chars like C++, C#, .NET, Node.js
                escaped = re.escape(skill.lower())
                
                # If single letter like C or R, require strict boundary
                if len(skill) == 1:
                    pattern = rf'(?<![a-zA-Z0-9+#])\b{escaped}\b(?![a-zA-Z0-9+#])'
                elif skill.endswith("+") or skill.endswith("#") or skill.startswith("."):
                    pattern = rf'(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])'
                else:
                    pattern = rf'\b{escaped}\b'

                if re.search(pattern, text_lower):
                    canonical_name = SKILL_SYNONYMS.get(skill.lower(), skill)
                    cat_matched.append(canonical_name)
                    all_detected.add(canonical_name)

            if cat_matched:
                categorized_skills[category] = sorted(list(set(cat_matched)))

        return categorized_skills, sorted(list(all_detected))

    def _extract_experience(self, exp_text: str) -> Tuple[List[ExperienceEntry], float]:
        """Extracts experience entries and estimates total years of experience."""
        entries: List[ExperienceEntry] = []
        if not exp_text or not exp_text.strip():
            return entries, 0.0

        # Look for date patterns in experience text
        date_pattern = re.compile(
            r'(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(?:19|20)\d{2}\s*(?:[-–—to\s]+)\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(?:(?:19|20)\d{2}|present|current|now)',
            re.IGNORECASE
        )

        blocks = re.split(r'\n{2,}', exp_text)
        current_year = datetime.now().year

        total_years = 0.0
        parsed_ranges: List[Tuple[float, float]] = []

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            date_match = date_pattern.search(block)
            date_range_str = date_match.group(0) if date_match else ""
            
            title = lines[0]
            company = lines[1] if len(lines) > 1 else ""
            highlights = lines[2:] if len(lines) > 2 else []

            duration = 0.0
            if date_range_str:
                duration = self._compute_duration_years(date_range_str, current_year)
                if duration > 0:
                    parsed_ranges.append((0, duration))

            entries.append(ExperienceEntry(
                title=title[:80],
                company=company[:80],
                date_range=date_range_str,
                duration_years=round(duration, 1),
                description="\n".join(highlights[:4]),
                highlights=highlights
            ))

        # Calculate total accumulated years
        if parsed_ranges:
            total_years = sum(d for _, d in parsed_ranges)
        else:
            total_years = self._calculate_years_from_text(exp_text)

        # Cap realistic career years to 35
        total_years = min(max(total_years, 0.0), 35.0)
        return entries, total_years

    def _compute_duration_years(self, range_str: str, current_year: int) -> float:
        """Calculates years from a date range string."""
        years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', range_str)]
        if not years:
            return 0.0
        
        start_year = min(years)
        if any(w in range_str.lower() for w in ["present", "current", "now"]):
            end_year = current_year
        elif len(years) >= 2:
            end_year = max(years)
        else:
            end_year = start_year + 1

        return max(float(end_year - start_year), 0.5)

    def _calculate_years_from_text(self, text: str) -> float:
        """Heuristic calculation of total years of experience from explicit mentions or year bounds."""
        # Check explicit statements: e.g. "5+ years of experience", "7 years in software"
        mention_pattern = re.compile(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|in)', re.IGNORECASE)
        match = mention_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        # Look for all 4-digit years in the text
        all_years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', text)]
        valid_years = [y for y in all_years if 1990 <= y <= datetime.now().year]
        if len(valid_years) >= 2:
            span = max(valid_years) - min(valid_years)
            # Return plausible span
            return min(float(span), 25.0)

        return 0.0

    def _extract_education(self, edu_text: str) -> List[EducationEntry]:
        """Extracts degrees, university names, and graduation years."""
        entries: List[EducationEntry] = []
        if not edu_text or not edu_text.strip():
            return entries

        lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
        
        for line in lines:
            detected_degree = ""
            for pattern, canonical in DEGREE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    detected_degree = canonical
                    break
            
            # Look for year in the line
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', line)
            year_str = year_match.group(0) if year_match else ""

            # Check for major/field of study
            field_match = re.search(
                r'(?:in|of)\s+([A-Za-z\s]+(?:Computer\s+Science|Information\s+Technology|Engineering|Data\s+Science|Software|Mathematics|Physics|Business|Economics|Finance)[A-Za-z\s]*)',
                line,
                re.IGNORECASE
            )
            field_str = field_match.group(1).strip() if field_match else ""

            if detected_degree or year_str or any(kw in line.lower() for kw in ["university", "college", "institute", "school", "bachelor", "master", "degree"]):
                entries.append(EducationEntry(
                    degree=detected_degree or "Degree / Qualification",
                    institution=line[:70],
                    year=year_str,
                    field_of_study=field_str,
                    details=line
                ))

        return entries[:4]

    def _extract_projects(self, proj_text: str) -> List[str]:
        if not proj_text or not proj_text.strip():
            return []
        lines = [l.strip().lstrip("•-* ") for l in proj_text.split("\n") if len(l.strip()) > 15]
        return lines[:6]

    def _extract_certifications(self, cert_text: str) -> List[str]:
        if not cert_text or not cert_text.strip():
            return []
        
        common_certs = [
            "AWS Certified Solutions Architect", "AWS Certified Developer", "AWS Certified Cloud Practitioner",
            "Certified Kubernetes Administrator (CKA)", "Certified Kubernetes Application Developer (CKAD)",
            "Microsoft Certified: Azure Fundamentals", "Microsoft Certified: Azure Solutions Architect",
            "Google Cloud Certified Professional Cloud Architect", "PMP", "Project Management Professional",
            "Certified ScrumMaster (CSM)", "CompTIA Security+", "CISSP", "Terraform Associate"
        ]

        found_certs = []
        for cert in common_certs:
            if re.search(rf'\b{re.escape(cert)}\b', cert_text, re.IGNORECASE):
                found_certs.append(cert)

        # Also extract lines under certifications section
        lines = [l.strip().lstrip("•-* ") for l in cert_text.split("\n") if 10 <= len(l.strip()) <= 80]
        for line in lines[:5]:
            if line not in found_certs and any(w in line.lower() for w in ["certified", "certificate", "certification", "license", "aws", "azure", "gcp", "scrum"]):
                found_certs.append(line)

        return list(dict.fromkeys(found_certs))[:6]
