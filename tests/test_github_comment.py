from unittest.mock import patch

import httpx

from app.github_comments import (
    get_pull_request_comments,
    post_pull_request_comment,
)


def test_get_pull_request_comments_handles_connection_error():
    with patch(
        "app.github_comments.httpx.get",
        side_effect=httpx.RequestError("Connection failed"),
    ):
        try:
            get_pull_request_comments("owner", "repo", 1)
            assert False
        except RuntimeError as e:
            assert "Failed to connect to GitHub" in str(e)


def test_post_pull_request_comment_handles_connection_error():
    with patch(
        "app.github_comments.httpx.post",
        side_effect=httpx.RequestError("Connection failed"),
    ):
        try:
            post_pull_request_comment(
                "owner",
                "repo",
                1,
                "Test comment",
            )
            assert False
        except RuntimeError as e:
            assert "Failed to connect to GitHub" in str(e)