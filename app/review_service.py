import os

from dotenv import load_dotenv

from app.github_client import get_pull_request_files
from app.ai_reviewer import review_code

load_dotenv()


def review_pull_request(owner: str, repo: str, pull_number: int):
    files = get_pull_request_files(owner, repo, pull_number)

    reviews = []

    for file in files:
        patch = file.get("patch")

        if not patch:
            continue

        review = review_code(patch)

        reviews.append({
            "filename": file["filename"],
            "review": review,
        })

    return reviews




