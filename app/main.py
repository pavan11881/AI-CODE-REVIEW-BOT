from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from app.github_client import get_pull_request
from app.review_service import review_pull_request
from app.github_comments import (
    get_pull_request_comments,
    post_pull_request_comment,
)

load_dotenv()

app = FastAPI(
    title="AI Code Review Bot",
    description="AI-powered GitHub Pull Request code reviewer",
    version="1.0.0",
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
):
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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )