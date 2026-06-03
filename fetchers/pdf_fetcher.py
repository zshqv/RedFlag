import os
import re
import pdfplumber


def fetch_pdf(file_path):
    """
    Extract text from a local PDF file page by page using pdfplumber.

    Args:
        file_path: Path to PDF file (can be absolute or relative)

    Returns:
        {
            "ticker": filename,
            "exchange": "Manual PDF",
            "latest": {"text": full_text, "date": "Manual"},
            "previous": {"text": "", "date": "N/A"}
        }
    """
    if not os.path.exists(file_path):
        print(f"[RedFlag] Error: PDF file not found: {file_path}")
        return None

    try:
        full_text = ""
        section_text = ""
        current_section = None

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""

                lines = page_text.split('\n')
                for line in lines:
                    line_stripped = line.strip()

                    if not line_stripped:
                        full_text += "\n"
                        section_text += "\n"
                        continue

                    is_all_caps = line_stripped.isupper() and len(line_stripped) > 3

                    if is_all_caps:
                        if current_section:
                            full_text += f"\n--- END {current_section} ---\n"
                        current_section = line_stripped
                        full_text += f"\n--- START {current_section} ---\n"
                        section_text = ""
                    else:
                        full_text += line + "\n"
                        section_text += line + "\n"

        filename = os.path.basename(file_path).replace('.pdf', '')

        return {
            "ticker": filename,
            "exchange": "Manual PDF",
            "latest": {"text": full_text, "date": "Manual"},
            "previous": {"text": "", "date": "N/A"}
        }

    except Exception as e:
        print(f"[RedFlag] Error reading PDF: {e}")
        return None
