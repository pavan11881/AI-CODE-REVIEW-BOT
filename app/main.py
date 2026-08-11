import logging
import os
import secrets

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header

from app.github_client import get_pull_request
from app.review_service import review_pull_request
from app.github_comments import (
    get_pull_request_comments,
    post_pull_request_comment,
)

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Code Review Bot",
    description="AI-powered GitHub Pull Request code reviewer",
    version="1.0.0",
)


def verify_api_key(
    authorization: str | None = Header(default=None),
):
    expected_key = os.getenv("AI_REVIEW_API_KEY")

    if not expected_key:
        logger.error("AI_REVIEW_API_KEY is not configured")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header",
        )

    provided_key = authorization.removeprefix("Bearer ").strip()

    if not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )


@app.get("/")
def root():
    return {"message": "AI Code Review Bot is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/review/{owner}/{repo}/{pull_number}")
def review_pull_request_endpoint(
    owner: str,
    repo: str,
    pull_number: int,
    authorization: str | None = Header(default=None),
):
    verify_api_key(authorization)

    try:
        pull_request = get_pull_request(
            owner,
            repo,
            pull_number,
        )

        commit_sha = pull_request["head"]["sha"]

        reviews = review_pull_request(
            owner,
            repo,
            pull_number,
            commit_sha,
        )

        if not reviews:
            return {
                "message": "No reviewable code changes found.",
                "commit_sha": commit_sha,
                "files_reviewed": 0,
                "comments_posted": 0,
                "comments": [],
            }

        existing_comments = get_pull_request_comments(
            owner,
            repo,
            pull_number,
        )

        comments = []
        skipped_files = []

        for item in reviews:
            filename = item["filename"]

            review_marker = (
                f"AI_REVIEW_COMMIT: {commit_sha}\n"
                f"AI_REVIEW_FILE: {filename}"
            )

            already_reviewed = any(
                review_marker in comment.get("body", "")
                for comment in existing_comments
            )

            if already_reviewed:
                skipped_files.append(filename)
                continue

            comment = (
                "## AI Code Review\n\n"
                f"### File: `{filename}`\n\n"
                f"{item['review']}\n\n"
                "---\n\n"
                "**Review metadata**\n\n"
                "```text\n"
                f"{review_marker}\n"
                "```\n"
            )

            result = post_pull_request_comment(
                owner,
                repo,
                pull_number,
                comment,
            )

            comments.append(
                {
                    "filename": filename,
                    "comment_url": result["html_url"],
                }
            )

        return {
            "message": "Code review completed successfully.",
            "commit_sha": commit_sha,
            "files_reviewed": len(reviews),
            "comments_posted": len(comments),
            "skipped_already_reviewed": len(skipped_files),
            "comments": comments,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error while reviewing PR %s/%s#%s",
            owner,
            repo,
            pull_number,
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )