from fastapi import FastAPI

app = FastAPI(
    title="ResQNet API",
    description="AI-Powered Disaster Management & Emergency Response Platform",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to ResQNet API",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "project": "ResQNet"
    }