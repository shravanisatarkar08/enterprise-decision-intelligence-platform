from fastapi import FastAPI

app = FastAPI(
    title="Enterprise Decision Intelligence Platform API",
    description="Backend API for the Enterprise Decision Intelligence Platform",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to Enterprise Decision Intelligence Platform",
        "status": "Backend is running successfully 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }