from unittest.mock import patch

from app.review_service import review_pull_request


def test_review_skips_deleted_files():
    files = [
        {
            "filename": "deleted.py",
            "status": "removed",
            "patch": "@@ -1,2 +0,0 @@",
        },
        {
            "filename": "main.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-old\n+new",
        },
    ]

    with patch(
        "app.review_service.get_pull_request_files",
        return_value=files,
    ), patch(
        "app.review_service.review_code",
        return_value="Looks good",
    ) as mock_review:

        result = review_pull_request(
            "owner",
            "repo",
            1,
            "abc123",
        )

    assert len(result) == 1
    assert result[0]["filename"] == "main.py"
    mock_review.assert_called_once()


def test_review_skips_unsupported_files():
    files = [
        {
            "filename": "README.md",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-old\n+new",
        },
        {
            "filename": "main.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-old\n+new",
        },
    ]

    with patch(
        "app.review_service.get_pull_request_files",
        return_value=files,
    ), patch(
        "app.review_service.review_code",
        return_value="Looks good",
    ) as mock_review:

        result = review_pull_request(
            "owner",
            "repo",
            1,
            "abc123",
        )

    assert len(result) == 1
    assert result[0]["filename"] == "main.py"
    mock_review.assert_called_once()
    print("Testing second commit")
