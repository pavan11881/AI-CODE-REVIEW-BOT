from unittest.mock import patch

from app.github_client import (
    get_pull_request,
    get_pull_request_files,
)


def test_get_pull_request_files_handles_pagination():
    first_page = [
        {
            "filename": f"file{i}.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-old\n+new",
        }
        for i in range(1, 101)
    ]

    second_page = [
        {
            "filename": "file101.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-old\n+new",
        }
    ]

    with patch("app.github_client.httpx.get") as mock_get:
        first_response = mock_get.return_value
        first_response.raise_for_status.return_value = None
        first_response.json.side_effect = [
            first_page,
            second_page,
        ]

        result = get_pull_request_files(
            "owner",
            "repo",
            1,
        )

    assert len(result) == 101
    assert result[0]["filename"] == "file1.py"
    assert result[-1]["filename"] == "file101.py"
    assert mock_get.call_count == 2


def test_get_pull_request_handles_github_http_error():
    with patch("app.github_client.httpx.get") as mock_get:
        mock_response = mock_get.return_value

        mock_response.raise_for_status.side_effect = Exception(
            "GitHub API error"
        )

        try:
            get_pull_request("owner", "repo", 1)
            assert False
        except Exception as e:
            assert "GitHub API error" in str(e)


def test_get_pull_request_files_handles_connection_error():
    import httpx

    with patch(
        "app.github_client.httpx.get",
        side_effect=httpx.RequestError("Connection failed"),
    ):
        try:
            get_pull_request_files("owner", "repo", 1)
            assert False
        except RuntimeError as e:
            assert "Failed to connect to GitHub" in str(e)