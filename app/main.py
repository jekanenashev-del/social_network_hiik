from fastapi import FastAPI
from app.api import games

app = FastAPI(title="Games")
app.include_router(games.router, prefix="/games", tags=["games"])