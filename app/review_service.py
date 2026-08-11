from dotenv import load_dotenv

from app.github_client import (
    get_file_content,
    get_pull_request_files,
)
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
    commit_sha: str,
):
    """
    Review supported source files changed in the specified commit.

    The complete file content at commit_sha is used for deterministic
    static analysis, while the GitHub patch is still supplied to the
    AI reviewer so it knows what changed.
    """

    files = get_pull_request_files(
        owner,
        repo,
        pull_number,
        commit_sha,
    )

    reviews = []

    for file in files:
        filename = file.get("filename")
        patch = file.get("patch")
        status = file.get("status")

        if not filename:
            continue

        if status == "removed":
            continue

        if not is_reviewable_file(filename):
            continue

        if not patch:
            continue

        try:
            file_content = get_file_content(
                owner,
                repo,
                filename,
                commit_sha,
            )
        except RuntimeError:
            file_content = patch

        review_input = (
            f"FULL FILE CONTENT:\n"
            f"{file_content}\n\n"
            f"CHANGED DIFF:\n"
            f"{patch}"
        )

        review = review_code(review_input)

        reviews.append(
            {
                "filename": filename,
                "review": review,
            }
        )

    return reviews