from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers.assets import router as assets_router
from app.routers.importer import router as importer_router
from app.routers.relationships import router as relationships_router
from app.routers.ai import router as ai_router


app = FastAPI(
    title="Asset Management System"
)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

app.include_router(assets_router)
app.include_router(importer_router)
app.include_router(relationships_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {
        "message": "Asset Management API is running"
    }