from pathlib import Path

from dotenv import load_dotenv

from app.github_client import get_pull_request_files
from app.ai_reviewer import review_code

load_dotenv()


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
}


def is_reviewable_file(filename: str) -> bool:
    """Return True when the file is a supported source-code file."""
    extension = Path(filename).suffix.lower()
    return extension in SUPPORTED_EXTENSIONS


def review_pull_request(owner: str, repo: str, pull_number: int):
    files = get_pull_request_files(owner, repo, pull_number)

    reviews = []

    for file in files:
        filename = file["filename"]

        if not is_reviewable_file(filename):
            continue

        patch = file.get("patch")

        if not patch:
            continue

        review = review_code(patch)

        reviews.append({
            "filename": filename,
            "review": review,
        })

    return reviews


