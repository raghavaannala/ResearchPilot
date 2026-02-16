from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from config import get_settings
from db.database import init_db
from api.routes.papers import router as papers_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("researchpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ResearchPilot API...")
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    await init_db()
    logger.info("Database initialized.")
    yield
    # Shutdown
    logger.info("Shutting down ResearchPilot API...")


app = FastAPI(
    title="ResearchPilot API",
    description="Multi-agent AI research intelligence system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(papers_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "researchpilot"}
