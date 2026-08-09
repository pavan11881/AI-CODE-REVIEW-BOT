from dotenv import load_dotenv

from app.github_client import get_pull_request_files
from app.ai_reviewer import review_code

load_dotenv()


def review_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    commit_sha: str,
):
    """
    Review only the files changed in the specified commit.
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

        # Skip files without a patch.
        if not filename or not patch:
            continue

        review = review_code(patch)

        reviews.append(
            {
                "filename": filename,
                "review": review,
            }
        )

    return reviews
