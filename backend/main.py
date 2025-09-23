from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Import routers and modules
from backend.auth_routes import router as auth_router
from backend.movie_routes import router as movie_router
from backend import database
from backend import database_models as models
from backend.celery_app import celery_app

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Cineo AI - Movie Generator", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(movie_router, prefix="/movies", tags=["movies"])

@app.get("/")
async def root():
    return {"message": "Welcome to Cineo AI - Your AI Movie Generator"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
