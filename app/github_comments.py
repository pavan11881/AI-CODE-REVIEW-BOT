import httpx

from app.github_client import HEADERS


def post_pull_request_comment(
    owner: str,
    repo: str,
    pull_number: int,
    comment: str,
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{pull_number}/comments"
    )

    response = httpx.post(
        url,
        headers=HEADERS,
        json={"body": comment},
    )

    response.raise_for_status()

    return response.json()










