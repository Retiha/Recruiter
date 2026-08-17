"""End-to-End Integration test simulating full recruitment workflow."""
import json
import unittest
from pathlib import Path

from services.pdf_extractor import PDFExtractor
from services.resume_parser import ResumeParser
from services.job_parser import JobParser
from services.matcher import CandidateJobMatcher
from services.ranking import CandidateRanker
from utils.exporters import DataExporter


class TestFullRecruitmentPipeline(unittest.TestCase):
    def test_end_to_end_screening_and_ranking(self):
        sample_dir = Path("data/sample_resumes")
        sample_files = list(sample_dir.glob("*.pdf"))
        self.assertGreaterEqual(len(sample_files), 6, "Expected at least 6 sample PDF resumes.")

        # 1. Parse all sample resumes
        parser = ResumeParser()
        candidates = {}
        for fpath in sample_files:
            ext_res = PDFExtractor.extract_text(fpath)
            self.assertTrue(ext_res.success, f"Failed to extract {fpath.name}")
            self.assertFalse(ext_res.is_empty)
            profile = parser.parse(ext_res.text, file_name=ext_res.file_name, file_size_kb=ext_res.file_size_kb)
            self.assertTrue(profile.name != "Unknown Candidate", f"Failed to parse name for {fpath.name}")
            self.assertTrue(len(profile.all_skills) > 0, f"No skills parsed for {fpath.name}")
            candidates[profile.id] = profile

        self.assertEqual(len(candidates), 6)

        # 2. Load Jobs
        with open("data/default_jobs.json", "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

        job_parser = JobParser()
        python_job_raw = jobs_data[0]
        python_job = job_parser.parse_job(
            title=python_job_raw["title"],
            description=python_job_raw["description"],
            required_skills=python_job_raw["required_skills"],
            preferred_skills=python_job_raw.get("preferred_skills", []),
            min_experience_years=python_job_raw.get("min_experience_years", 5.0),
            seniority_level=python_job_raw.get("seniority_level", "Senior")
        )

        # 3. Match candidates against Python Job
        match_results = CandidateJobMatcher.match_all(list(candidates.values()), python_job)
        self.assertEqual(len(match_results), 6)

        # 4. Rank candidates
        ranked = CandidateRanker.rank_candidates(match_results)
        self.assertEqual(len(ranked), 6)
        self.assertEqual(ranked[0]["rank"], 1)

        # Top candidate for Python job should be Alex Rivera
        top_cand_name = ranked[0]["candidate_name"]
        self.assertIn("Alex", top_cand_name)
        self.assertGreaterEqual(ranked[0]["overall_score"], 80.0)
        self.assertEqual(ranked[0]["category"], "Excellent Match")

        # 5. Verify Dashboard Metrics Calculation
        metrics = CandidateRanker.calculate_dashboard_metrics(match_results, python_job)
        self.assertEqual(metrics["total_resumes"], 6)
        self.assertGreaterEqual(metrics["suitable_candidates"], 1)
        self.assertGreater(metrics["average_score"], 0.0)
        self.assertGreater(len(metrics["top_matching_skills"]), 0)

        # 6. Verify Exports
        csv_data = DataExporter.export_to_csv(ranked, candidates)
        self.assertIn("Alex Rivera", csv_data)
        self.assertIn("Rank", csv_data)
        self.assertIn("Python", csv_data)

        json_data = DataExporter.export_to_json(ranked, python_job)
        parsed_json = json.loads(json_data)
        self.assertEqual(parsed_json["total_candidates"], 6)
        self.assertEqual(parsed_json["job_profile"]["title"], python_job.title)

        # 7. Verify Individual Report Card
        top_profile = candidates[ranked[0]["candidate_id"]]
        top_match_res = next(r for r in match_results if r.candidate_id == top_profile.id)
        report_md = DataExporter.generate_candidate_report(top_profile, top_match_res, python_job)
        self.assertIn(top_profile.name, report_md)
        self.assertIn("Skills Analysis", report_md)


if __name__ == "__main__":
    unittest.main()
