import httpx

from app.github_client import HEADERS


def get_pull_request_comments(
    owner: str,
    repo: str,
    pull_number: int,
):
    base_url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{pull_number}/comments"
    )

    all_comments = []
    page = 1

    while True:
        try:
            response = httpx.get(
                base_url,
                headers=HEADERS,
                params={
                    "page": page,
                    "per_page": 100,
                },
                timeout=30.0,
            )

            response.raise_for_status()

            comments = response.json()

            if not comments:
                break

            all_comments.extend(comments)

            if len(comments) < 100:
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

    return all_comments


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

    try:
        response = httpx.post(
            url,
            headers=HEADERS,
            json={"body": comment},
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