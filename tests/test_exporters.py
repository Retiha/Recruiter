"""Tests for DataExporter utilities."""
import json
import unittest
from models.candidate import CandidateProfile
from models.job import JobDescription, MatchResult
from utils.exporters import DataExporter


class TestDataExporter(unittest.TestCase):
    def test_export_to_csv(self):
        ranked = [
            {
                "rank": 1,
                "candidate_id": "c1",
                "candidate_name": "Alice Smith",
                "email": "alice@example.com",
                "phone": "+1 555-0100",
                "overall_score": 88.5,
                "category": "Excellent Match",
                "skills_score": 55.0,
                "experience_score": 20.0,
                "similarity_score": 13.5,
                "matching_required_skills": ["Python", "FastAPI"],
                "missing_required_skills": [],
                "matching_preferred_skills": ["Docker"],
                "missing_preferred_skills": [],
                "candidate_experience_years": 5.0,
                "required_experience_years": 4.0,
                "strengths": ["Matches Python"],
                "improvement_areas": []
            }
        ]

        profiles = {
            "c1": CandidateProfile(
                id="c1",
                file_name="alice.pdf",
                name="Alice Smith",
                email="alice@example.com",
                phone="+1 555-0100"
            )
        }

        csv_output = DataExporter.export_to_csv(ranked, profiles)
        self.assertIn("Rank", csv_output)
        self.assertIn("Alice Smith", csv_output)
        self.assertIn("alice@example.com", csv_output)
        self.assertIn("88.5", csv_output)
        self.assertIn("Excellent Match", csv_output)

    def test_export_to_json(self):
        ranked = [
            {
                "rank": 1,
                "candidate_id": "c1",
                "candidate_name": "Bob Jones",
                "overall_score": 75.0,
                "category": "Good Match"
            }
        ]
        job = JobDescription(title="Frontend Engineer")

        json_output = DataExporter.export_to_json(ranked, job)
        data = json.loads(json_output)
        self.assertEqual(data["total_candidates"], 1)
        self.assertEqual(data["job_profile"]["title"], "Frontend Engineer")
        self.assertEqual(data["candidates"][0]["candidate_name"], "Bob Jones")


if __name__ == "__main__":
    unittest.main()
