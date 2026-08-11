from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "AI Code Review Bot is running"
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }


def test_review_endpoint_posts_comment():
    mock_pull_request = {
        "head": {
            "sha": "abc123"
        }
    }

    mock_reviews = [
        {
            "filename": "app/test_code.py",
            "review": "### BUG\n\nDivision by zero risk.",
        }
    ]

    mock_comment = {
        "html_url": "https://github.com/test/comment/1"
    }

    with patch(
        "app.main.get_pull_request",
        return_value=mock_pull_request,
    ), patch(
        "app.main.review_pull_request",
        return_value=mock_reviews,
    ), patch(
        "app.main.get_pull_request_comments",
        return_value=[],
    ), patch(
        "app.main.post_pull_request_comment",
        return_value=mock_comment,
    ):
        response = client.post(
            "/review/test-owner/test-repo/1"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Code review completed successfully."
    assert data["commit_sha"] == "abc123"
    assert data["files_reviewed"] == 1
    assert data["comments_posted"] == 1
    assert data["skipped_already_reviewed"] == 0
    assert len(data["comments"]) == 1
    assert data["comments"][0]["filename"] == "app/test_code.py"


def test_review_endpoint_skips_already_reviewed_file():
    commit_sha = "abc123"
    filename = "app/test_code.py"

    review_marker = (
        f"AI_REVIEW_COMMIT: {commit_sha}\n"
        f"AI_REVIEW_FILE: {filename}"
    )

    mock_pull_request = {
        "head": {
            "sha": commit_sha
        }
    }

    mock_reviews = [
        {
            "filename": filename,
            "review": "No significant issues found.",
        }
    ]

    existing_comments = [
        {
            "body": f"Previous review\n{review_marker}"
        }
    ]

    with patch(
        "app.main.get_pull_request",
        return_value=mock_pull_request,
    ), patch(
        "app.main.review_pull_request",
        return_value=mock_reviews,
    ), patch(
        "app.main.get_pull_request_comments",
        return_value=existing_comments,
    ), patch(
        "app.main.post_pull_request_comment",
    ) as mock_post:
        response = client.post(
            "/review/test-owner/test-repo/1"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["files_reviewed"] == 1
    assert data["comments_posted"] == 0
    assert data["skipped_already_reviewed"] == 1
    assert data["comments"] == []

    mock_post.assert_not_called()