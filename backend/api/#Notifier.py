"""Compatibility FastAPI app for the notification endpoints."""

from fastapi import FastAPI

from backend.api.notifier import router

app = FastAPI(title="Bentley Budget Bot Notifications")
app.include_router(router)
