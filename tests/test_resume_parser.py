"""Tests for ResumeParser service."""
import unittest
from services.resume_parser import ResumeParser


class TestResumeParser(unittest.TestCase):
    def setUp(self):
        self.parser = ResumeParser()

    def test_resume_parser_contact_info(self):
        sample_text = """
        Jane Doe
        Senior Software Engineer
        Email: jane.doe@example.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/janedoe-tech
        GitHub: github.com/janedoe-dev

        PROFESSIONAL SUMMARY
        Experienced engineer with 5 years building web applications.

        TECHNICAL SKILLS
        Python, Django, FastAPI, React, Docker, PostgreSQL, AWS, Git

        WORK EXPERIENCE
        Lead Developer — TechCorp
        2019 - Present
        • Developed microservices using Python and Docker.
        • Managed AWS infrastructure and PostgreSQL database.

        EDUCATION
        Bachelor of Science in Computer Science, MIT (2015 - 2019)
        """

        profile = self.parser.parse(sample_text, file_name="Jane_Doe_Resume.pdf", file_size_kb=45.2)

        self.assertIn("Jane", profile.name)
        self.assertEqual(profile.email, "jane.doe@example.com")
        self.assertIn("555", profile.phone)
        self.assertIn("linkedin", profile.links)
        self.assertIn("github", profile.links)
        self.assertIn("Python", profile.all_skills)
        self.assertIn("Docker", profile.all_skills)
        self.assertIn("FastAPI", profile.all_skills)
        self.assertGreaterEqual(profile.total_experience_years, 4.0)
        self.assertGreater(len(profile.education), 0)
        self.assertEqual(profile.education[0].degree, "Bachelor's Degree")

    def test_resume_parser_empty_text(self):
        profile = self.parser.parse("", file_name="empty.pdf")
        self.assertEqual(profile.name, "Unknown Candidate")
        self.assertEqual(profile.email, "")
        self.assertEqual(len(profile.all_skills), 0)

    def test_skill_boundary_matching(self):
        text = "We are going to React quickly to clear issues."
        _, all_skills = self.parser._extract_skills(text)
        self.assertNotIn("Go", all_skills)
        self.assertNotIn("C", all_skills)
        self.assertNotIn("R", all_skills)
        self.assertIn("React", all_skills)


if __name__ == "__main__":
    unittest.main()
