import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN is not configured")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pull_number}"
    )

    try:
        response = httpx.get(
            url,
            headers=HEADERS,
            timeout=30.0,
        )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"GitHub API error {e.response.status_code}: "
            f"{e.response.text}"
        ) from e

    except httpx.RequestError as e:
        raise RuntimeError(
            f"Failed to connect to GitHub: {e}"
        ) from e


def get_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int,
    commit_sha: str | None = None,
):
    """
    Get files changed in a Pull Request or a specific commit.

    If commit_sha is provided, only files changed in that commit
    are returned.

    If commit_sha is not provided, all files changed in the
    Pull Request are returned.

    Handles GitHub API pagination.
    """

    files = []
    page = 1

    while True:
        if commit_sha:
            url = (
                f"https://api.github.com/repos/"
                f"{owner}/{repo}/commits/{commit_sha}"
            )
        else:
            url = (
                f"https://api.github.com/repos/"
                f"{owner}/{repo}/pulls/{pull_number}/files"
            )

        try:
            response = httpx.get(
                url,
                headers=HEADERS,
                params={
                    "page": page,
                    "per_page": 100,
                },
                timeout=30.0,
            )

            response.raise_for_status()

            data = response.json()

            if commit_sha:
                page_files = data.get("files", [])
            else:
                page_files = data

            if not page_files:
                break

            files.extend(page_files)

            if len(page_files) < 100:
                break

            page += 1

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"GitHub API error {e.response.status_code}: "
                f"{e.response.text}"
            ) from e

        except httpx.RequestError as e:
            raise RuntimeError(
                f"Failed to connect to GitHub: {e}"
            ) from e

    return files


def get_file_content(
    owner: str,
    repo: str,
    path: str,
    commit_sha: str,
) -> str:
    """
    Get the contents of a file at a specific Git commit.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{path}"
    )

    try:
        response = httpx.get(
            url,
            headers=HEADERS,
            params={"ref": commit_sha},
            timeout=30.0,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("encoding") != "base64":
            raise RuntimeError(
                f"Unsupported GitHub file encoding for {path}"
            )

        import base64

        content = base64.b64decode(
            data["content"]
        ).decode("utf-8")

        return content

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"GitHub API error {e.response.status_code}: "
            f"{e.response.text}"
        ) from e

    except httpx.RequestError as e:
        raise RuntimeError(
            f"Failed to connect to GitHub: {e}"
        ) from e

    except (KeyError, ValueError, UnicodeDecodeError) as e:
        raise RuntimeError(
            f"Failed to decode GitHub file {path}: {e}"
        ) from e