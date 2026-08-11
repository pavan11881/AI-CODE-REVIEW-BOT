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
    return any(
        filename.lower().endswith(extension)
        for extension in SUPPORTED_EXTENSIONS
    )


def review_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
):
    """
    Review supported source files changed in the Pull Request.
    """

    files = get_pull_request_files(
        owner,
        repo,
        pull_number,
    )

    reviews = []

    for file in files:
        filename = file.get("filename")
        patch = file.get("patch")
        status = file.get("status")

        # Skip files without a filename.
        if not filename:
            continue

        # Skip deleted files.
        if status == "removed":
            continue

        # Skip unsupported file types.
        if not is_reviewable_file(filename):
            continue

        # Skip files without a patch.
        if not patch:
            continue

        review = review_code(patch)

        reviews.append(
            {
                "filename": filename,
                "review": review,
            }
        )

    return reviews