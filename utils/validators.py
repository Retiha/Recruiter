"""Validation utilities for PDF files, inputs, and job requisition data."""
import logging
from typing import Tuple, List, Optional, Any

logger = logging.getLogger("ai_recruiter.validators")

MAX_FILE_SIZE_MB = 15.0
MAX_FILE_SIZE_BYTES = int(MAX_FILE_SIZE_MB * 1024 * 1024)
PDF_MAGIC_NUMBER = b"%PDF-"


class PDFValidator:
    """Validates uploaded resume PDF files."""

    @classmethod
    def validate_file(cls, file_obj: Any) -> Tuple[bool, Optional[str]]:
        """
        Validates file type, size, and header signature.
        
        Args:
            file_obj: Streamlit UploadedFile or file-like object.
            
        Returns:
            (is_valid, error_message)
        """
        file_name = getattr(file_obj, "name", "unknown_file")
        
        # 1. Check extension
        if not file_name.lower().endswith(".pdf"):
            return False, f"'{file_name}' is not a PDF file. Please upload .pdf documents only."

        # 2. Check file size
        size = getattr(file_obj, "size", None)
        if size is not None and size > MAX_FILE_SIZE_BYTES:
            size_mb = round(size / (1024 * 1024), 2)
            return False, f"'{file_name}' ({size_mb} MB) exceeds maximum allowed file size of {MAX_FILE_SIZE_MB} MB."

        # 3. Check PDF magic header
        try:
            if hasattr(file_obj, "read") and hasattr(file_obj, "seek"):
                header = file_obj.read(5)
                file_obj.seek(0)
                if header != PDF_MAGIC_NUMBER:
                    return False, f"'{file_name}' appears to be corrupted or not a valid PDF file header."
        except Exception as e:
            logger.warning(f"Header validation error for {file_name}: {e}")

        return True, None


class JobValidator:
    """Validates job requisition form submissions."""

    @classmethod
    def validate_job_input(
        cls,
        title: str,
        description: str,
        required_skills: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validates job title and description."""
        errors = []
        if not title or len(title.strip()) < 3:
            errors.append("Job Title must be at least 3 characters long.")

        if not description or len(description.strip()) < 20:
            errors.append("Job Description should contain at least 20 characters of detail.")

        return len(errors) == 0, errors
