# AI Code Review Bot

An AI-powered GitHub Pull Request code review system built with **FastAPI, Ollama, GitHub API, and GitHub Actions**.

The bot automatically receives GitHub Pull Request events, retrieves the changed files, analyzes supported source code using an AI reviewer, and posts review comments directly to the Pull Request.

## Features

* Automated GitHub Pull Request code reviews
* AI-powered code analysis using Ollama
* FastAPI backend
* GitHub REST API integration
* GitHub Actions automation
* Secure API-key authentication
* Commit-specific review tracking
* Duplicate-review prevention
* Review only supported source-code files
* Deleted-file filtering
* GitHub API pagination handling
* Error handling and server-side logging
* Automated test suite

## Architecture

```text
GitHub Pull Request
        |
        v
GitHub Actions
        |
        | AI_REVIEW_BOT_URL
        | AI_REVIEW_API_KEY
        v
      ngrok
        |
        v
   FastAPI Backend
        |
        +--------------------+
        |                    |
        v                    v
   GitHub API            Ollama
        |                    |
        |                    v
        |               AI Review
        |                    |
        +---------+----------+
                  |
                  v
        Review Comments
                  |
                  v
        GitHub Pull Request
```

## Tech Stack

| Technology      | Purpose                               |
| --------------- | ------------------------------------- |
| Python          | Application development               |
| FastAPI         | REST API backend                      |
| Uvicorn         | ASGI server                           |
| Ollama          | Local AI inference                    |
| GitHub REST API | Pull Request and comment integration  |
| GitHub Actions  | CI/CD automation                      |
| ngrok           | Public tunnel to local FastAPI server |
| httpx           | HTTP client                           |
| python-dotenv   | Environment configuration             |
| pytest          | Automated testing                     |

## Project Structure

```text
AI-CODE-REVIEW-BOT/
|
??? .github/
?   ??? workflows/
?       ??? ai-review.yml
|
??? app/
?   ??? ai_reviewer.py
?   ??? github_client.py
?   ??? github_comments.py
?   ??? main.py
?   ??? review_service.py
|
??? tests/
?   ??? test_ai_reviewer.py
?   ??? test_github_client.py
?   ??? test_github_comment.py
?   ??? test_main.py
?   ??? test_review_service.py
|
??? ai_review_sample.py
??? .env
??? .gitignore
??? pytest.ini
??? requirements.txt
??? README.md
```

## Prerequisites

Install the following:

* Python 3.x
* Git
* Ollama
* A GitHub repository
* A GitHub Personal Access Token with the permissions required to read Pull Requests and create Pull Request comments
* ngrok for exposing the local FastAPI server during development

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/pavan11881/AI-CODE-REVIEW-BOT.git
cd AI-CODE-REVIEW-BOT
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```cmd
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root.

```env
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name
AI_REVIEW_API_KEY=your_generated_secret
```

The `.env` file must never be committed to Git.

The repository `.gitignore` already excludes `.env`.

## Ollama Setup

Install Ollama and make sure the Ollama service is running.

Pull the model used by the application:

```bash
ollama pull llama3.2:3b
```

Verify that Ollama is available before starting the review bot.

## Run the FastAPI Backend

Activate the virtual environment:

```cmd
venv\Scripts\activate
```

Start the server:

```cmd
uvicorn app.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

Check the health endpoint:

```cmd
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

## API Authentication

The review endpoint is protected with a Bearer API key.

The server expects:

```text
Authorization: Bearer <AI_REVIEW_API_KEY>
```

Requests without a valid key are rejected with HTTP `401`.

The API key comparison uses constant-time comparison through Python's `secrets.compare_digest()`.

Unexpected server errors return a generic HTTP `500` response while the detailed exception is logged server-side.

## Review Endpoint

The main endpoint is:

```text
POST /review/{owner}/{repo}/{pull_number}
```

Example:

```cmd
curl -X POST ^
  -H "Authorization: Bearer YOUR_API_KEY" ^
  http://127.0.0.1:8000/review/OWNER/REPOSITORY/1
```

The service:

1. Retrieves the Pull Request.
2. Determines the current commit SHA.
3. Retrieves changed files.
4. Filters unsupported and deleted files.
5. Sends reviewable code to the AI reviewer.
6. Retrieves existing Pull Request comments.
7. Checks whether the current commit/file was already reviewed.
8. Posts new review comments when necessary.
9. Returns a summary of the review operation.

## Duplicate Review Prevention

Each posted review contains metadata identifying the commit and file:

```text
AI_REVIEW_COMMIT: <commit_sha>
AI_REVIEW_FILE: <filename>
```

Before posting a new comment, the application checks existing Pull Request comments for this marker.

If the same commit/file has already been reviewed, the file is skipped.

This prevents duplicate comments when GitHub Actions or the review endpoint is triggered multiple times for the same commit.

## GitHub Actions

The workflow is located at:

```text
.github/workflows/ai-review.yml
```

It runs when a Pull Request is:

* opened
* synchronized
* reopened

The workflow sends an authenticated request to the FastAPI review endpoint.

Required GitHub repository secrets:

```text
AI_REVIEW_BOT_URL
AI_REVIEW_API_KEY
```

Configure them under:

```text
Repository
? Settings
? Secrets and variables
? Actions
```

The workflow uses the secrets without exposing their values in the logs.

## ngrok Development Setup

For local development, expose FastAPI through ngrok:

```cmd
ngrok http 8000
```

ngrok provides a public HTTPS forwarding URL.

Configure that URL as the GitHub Actions secret:

```text
AI_REVIEW_BOT_URL
```

For example:

```text
https://your-ngrok-domain.ngrok-free.dev
```

Verify the tunnel:

```cmd
curl https://your-ngrok-domain.ngrok-free.dev/health
```

Expected response:

```json
{"status":"healthy"}
```

### Important

ngrok is being used here as a development/testing tunnel.

For a production deployment, the FastAPI service should be hosted on a stable HTTPS endpoint rather than relying on a local development machine and temporary ngrok URL.

## Testing

Run the complete automated test suite:

```cmd
pytest -v
```

The current test suite contains **18 tests** covering:

* AI review behavior
* Division-by-zero detection
* Ollama failure handling
* GitHub API errors
* GitHub API connection failures
* GitHub API pagination
* Commit SHA handling
* GitHub comment failures
* FastAPI root endpoint
* FastAPI health endpoint
* Successful review requests
* Duplicate-review prevention
* Missing API-key rejection
* Invalid API-key rejection
* Internal error handling
* Deleted-file filtering
* Unsupported-file filtering

Current validation:

```text
18 passed
```

## Security

The application includes several security measures:

* `.env` is excluded from Git.
* GitHub Actions secrets are used for sensitive configuration.
* The review endpoint requires API-key authentication.
* API keys are compared using `secrets.compare_digest()`.
* Authentication failures return HTTP `401`.
* Internal exceptions are logged server-side.
* Internal exception details are not returned to API clients.

Never commit:

```text
.env
```

or any GitHub token/API key to the repository.

If a secret is accidentally committed, revoke and replace it immediately.

## Current Limitations

This project currently uses a local FastAPI server exposed through ngrok for GitHub integration testing.

For a production deployment, the following should be considered:

* Deploy FastAPI to a persistent HTTPS server.
* Use a stable domain instead of a temporary ngrok URL.
* Add stronger request authentication and/or webhook signature verification.
* Configure structured application logging.
* Pin production dependency versions.
* Add rate limiting.
* Add monitoring and health checks.
* Use a production ASGI deployment configuration.
* Rotate secrets periodically.

## Validation Status

The current implementation has been validated through:

```text
18 automated tests passing
FastAPI health endpoint verified
ngrok tunnel verified
GitHub Actions integration verified
API authentication verified
GitHub API integration verified
Duplicate-review prevention verified
Error handling verified
```

The complete tested flow is:

```text
GitHub Pull Request
        ?
GitHub Actions
        ?
Authenticated API request
        ?
ngrok
        ?
FastAPI
        ?
GitHub API
        ?
AI reviewer / Ollama
        ?
Duplicate detection
        ?
GitHub Pull Request comment
```

## License

This project is currently a personal/portfolio project. Add an explicit open-source license if you intend to distribute the repository under specific reuse terms.
