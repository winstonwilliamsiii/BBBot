from fastapi import FastAPI

app = FastAPI(
    title="Bentley Budget Bot API",
    version="0.1.0",
    description="Minimal FastAPI service for Bentley Budget Bot.",
)


@app.get("/")
async def root():
    return {"message": "Bentley Budget Bot!"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}