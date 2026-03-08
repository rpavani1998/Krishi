from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
import uvicorn
import os

from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Agricultural Decision Support System",
    version="0.1.0",
    debug=settings.DEBUG
)

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "*" # Allow all for prototype
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
