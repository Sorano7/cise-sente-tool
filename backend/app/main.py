from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import datetime, objects, pathfind, vessels, language

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

app.include_router(datetime.router, prefix="/api/datetime")
app.include_router(objects.router, prefix="/api/objects")
app.include_router(pathfind.router, prefix="/api/pathfind")
app.include_router(vessels.router, prefix="/api/vessels")
app.include_router(language.router, prefix="/api/language")