"""PDF Text Extraction service using PyMuPDF (fitz) with robust format and error handling."""
import io
import logging
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, BinaryIO, Optional, Dict, Any

import fitz  # PyMuPDF

logger = logging.getLogger("ai_recruiter.pdf_extractor")


@dataclass
class PDFExtractionResult:
    """Encapsulates the result of a PDF text extraction operation."""
    success: bool
    text: str = ""
    page_count: int = 0
    file_name: str = ""
    file_size_kb: float = 0.0
    is_empty: bool = False
    is_scanned_likely: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class PDFExtractor:
    """High-performance and resilient PDF text extractor."""

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Normalizes unicode characters, ligatures, and cleans irregular whitespace."""
        if not raw_text:
            return ""
        
        # Normalize unicode (e.g. fi, fl ligatures, smart quotes)
        normalized = unicodedata.normalize("NFKD", raw_text)
        
        # Replace common strange symbols or form feed characters
        normalized = normalized.replace("\x0c", "\n").replace("\r\n", "\n").replace("\r", "\n")
        
        # Collapse excessive blank lines while preserving paragraph boundaries
        lines = [line.strip() for line in normalized.split("\n")]
        cleaned_lines = []
        consecutive_empty = 0
        for line in lines:
            if not line:
                consecutive_empty += 1
                if consecutive_empty <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_empty = 0
                cleaned_lines.append(line)
                
        return "\n".join(cleaned_lines).strip()

    @classmethod
    def extract_text(
        cls,
        file_input: Union[str, Path, bytes, BinaryIO, Any],
        file_name: Optional[str] = None
    ) -> PDFExtractionResult:
        """
        Extracts text from a PDF file path, raw bytes, or Streamlit UploadedFile.
        
        Args:
            file_input: Path, bytes, or file-like object.
            file_name: Optional explicit filename.
            
        Returns:
            PDFExtractionResult with extracted text, page count, and status metadata.
        """
        resolved_name = file_name or "uploaded_resume.pdf"
        size_kb = 0.0
        doc = None

        try:
            # Handle Streamlit UploadedFile or file-like objects
            if hasattr(file_input, "read") and hasattr(file_input, "name"):
                resolved_name = file_name or getattr(file_input, "name", "uploaded_resume.pdf")
                file_bytes = file_input.read()
                size_kb = round(len(file_bytes) / 1024.0, 2)
                # Reset stream position if possible
                if hasattr(file_input, "seek"):
                    file_input.seek(0)
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            # Handle raw bytes
            elif isinstance(file_input, bytes):
                size_kb = round(len(file_input) / 1024.0, 2)
                doc = fitz.open(stream=file_input, filetype="pdf")
                
            # Handle file paths
            elif isinstance(file_input, (str, Path)):
                path_obj = Path(file_input)
                if not path_obj.exists():
                    return PDFExtractionResult(
                        success=False,
                        file_name=path_obj.name,
                        error_message=f"File not found at path: {file_input}"
                    )
                resolved_name = file_name or path_obj.name
                size_kb = round(path_obj.stat().st_size / 1024.0, 2)
                doc = fitz.open(str(path_obj))
            else:
                return PDFExtractionResult(
                    success=False,
                    file_name=resolved_name,
                    error_message=f"Unsupported file input type: {type(file_input)}"
                )

            # Check if PDF is encrypted
            if doc.is_encrypted:
                return PDFExtractionResult(
                    success=False,
                    file_name=resolved_name,
                    file_size_kb=size_kb,
                    error_message="The PDF file is encrypted or password-protected."
                )

            page_count = len(doc)
            if page_count == 0:
                return PDFExtractionResult(
                    success=False,
                    file_name=resolved_name,
                    file_size_kb=size_kb,
                    page_count=0,
                    is_empty=True,
                    error_message="The PDF document has 0 pages."
                )

            # Extract text per page
            extracted_pages = []
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                if page_text:
                    extracted_pages.append(page_text)

            full_text = "\n\n".join(extracted_pages)
            cleaned_text = cls.clean_text(full_text)
            
            # Extract metadata
            doc_meta = doc.metadata or {}
            cleaned_meta = {
                "author": doc_meta.get("author", ""),
                "title": doc_meta.get("title", ""),
                "creator": doc_meta.get("creator", ""),
                "producer": doc_meta.get("producer", ""),
                "creation_date": doc_meta.get("creationDate", ""),
            }

            # Check if text is empty (e.g. image-only / scanned PDF)
            if not cleaned_text.strip():
                return PDFExtractionResult(
                    success=True,
                    text="",
                    page_count=page_count,
                    file_name=resolved_name,
                    file_size_kb=size_kb,
                    is_empty=True,
                    is_scanned_likely=True,
                    metadata=cleaned_meta,
                    error_message="No selectable text found in the PDF. It might be a scanned image or photo."
                )

            return PDFExtractionResult(
                success=True,
                text=cleaned_text,
                page_count=page_count,
                file_name=resolved_name,
                file_size_kb=size_kb,
                is_empty=False,
                is_scanned_likely=False,
                metadata=cleaned_meta,
            )

        except fitz.FileDataError as e:
            logger.error(f"PyMuPDF FileDataError for {resolved_name}: {e}")
            return PDFExtractionResult(
                success=False,
                file_name=resolved_name,
                file_size_kb=size_kb,
                error_message="Invalid or corrupted PDF file structure."
            )
        except Exception as e:
            logger.error(f"Unexpected error extracting PDF {resolved_name}: {e}")
            return PDFExtractionResult(
                success=False,
                file_name=resolved_name,
                file_size_kb=size_kb,
                error_message=f"Failed to process PDF: {str(e)}"
            )
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass
