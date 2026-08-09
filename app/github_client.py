import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_pull_request(owner: str, repo: str, pull_number: int):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pull_number}"
    )

    response = httpx.get(
        url,
        headers=HEADERS,
    )

    response.raise_for_status()

    return response.json()


def get_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int,
    commit_sha: str,
):
    """
    Get files changed in a specific commit.

    This prevents the bot from reviewing every file in the
    Pull Request when only a new commit was added.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/commits/{commit_sha}"
    )

    response = httpx.get(
        url,
        headers=HEADERS,
    )

    response.raise_for_status()

    commit_data = response.json()

    return commit_data.get("files", [])