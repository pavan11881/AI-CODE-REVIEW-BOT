
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
    return {
        "message": "AI Code Review Bot is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


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
                "reviews": [],
            }

        comments = []

        existing_comments = get_pull_request_comments(
            owner,
            repo,
            pull_number,
        )

        review_marker = f"<!-- AI_REVIEW_COMMIT:{commit_sha} -->"

        existing_ai_reviews = {
            comment["body"]
            for comment in existing_comments
            if review_marker in comment.get("body", "")
        }

        for item in reviews:
            comment = f"""## AI Code Review

### File: `{item['filename']}`

{item['review']}

{review_marker}
"""

            if comment in existing_ai_reviews:
                continue

            result = post_pull_request_comment(
                owner,
                repo,
                pull_number,
                comment,
            )

            comments.append({
                "filename": item["filename"],
                "comment_url": result["html_url"],
            })

        return {
            "message": "Code review completed successfully.",
            "commit_sha": commit_sha,
            "files_reviewed": len(reviews),
            "comments": comments,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )