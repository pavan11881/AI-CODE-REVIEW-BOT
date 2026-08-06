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
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    response = httpx.get(url, headers=HEADERS)

    response.raise_for_status()

    return response.json()


def get_pull_request_files(owner: str, repo: str, pull_number: int):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"

    response = httpx.get(url, headers=HEADERS)

    response.raise_for_status()

    return response.json()