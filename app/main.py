from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.db import create_tables
from app.rag.retriever import retriever
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create database tables
    create_tables()

    # Load the local scientific knowledge base
    knowledge_file = (
        settings.DOCUMENTS_DIR / "knowledge.jsonl"
    )

    if knowledge_file.exists():
        try:
            retriever.ingest_jsonl(
                knowledge_file
            )
        except Exception as exc:
            print(
                f"Knowledge base loading warning: {exc}"
            )

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI Environmental Scientist for "
        "Biodiversity & Ecosystem Health"
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API routes
# ---------------------------------------------------------

app.include_router(router)


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Biodiversity Intelligence AI is running",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }