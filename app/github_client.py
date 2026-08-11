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
):
    """
    Get all files changed in a Pull Request.
    Handles GitHub API pagination.
    """

    files = []
    page = 1

    while True:
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

            page_files = response.json()

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