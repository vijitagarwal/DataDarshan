"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import query, upload

app = FastAPI(
    title="DataDarshan API",
    description="Conversational AI for Business Intelligence Dashboards",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api")
app.include_router(upload.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "DataDarshan"}
