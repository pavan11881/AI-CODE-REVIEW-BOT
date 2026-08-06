from fastapi import FastAPI

app = FastAPI(
    title="AI Code Review Bot",
    description="AI-powered GitHub Pull Request code reviewer",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "AI Code Review Bot is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }