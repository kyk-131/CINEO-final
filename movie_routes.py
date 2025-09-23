import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from . import database_models as models, database
from .auth_routes import get_current_user
from .tasks import generate_movie_scene, generate_movie_poster, generate_movie_trailer, generate_full_movie
from models.ai_models import text_to_script, storyboard, video_gen, lip_sync, audio, poster

router = APIRouter()

class MovieIdea(BaseModel):
    title: str
    genre: str
    style: str
    description: str

class SceneUpdate(BaseModel):
    scene_id: int
    action: str  # "accept" or "regenerate"

class MovieResponse(BaseModel):
    id: int
    title: str
    genre: str
    style: str
    description: str
    status: str
    script: Optional[List[Dict]]
    poster_url: Optional[str]
    trailer_url: Optional[str]
    video_url: Optional[str]

    class Config:
        from_attributes = True

class SceneResponse(BaseModel):
    id: int
    scene_number: int
    description: str
    storyboard_url: Optional[str]
    video_url: Optional[str]
    audio_url: Optional[str]
    status: str

    class Config:
        from_attributes = True

@router.post("/create", response_model=MovieResponse)
def create_movie(movie_idea: MovieIdea, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Step 1: Create movie from user idea"""
    # Check user credits
    user_credits = db.query(models.UserCredit).filter(models.UserCredit.user_id == current_user.id).first()
    if user_credits.credits < 40:
        raise HTTPException(status_code=400, detail="Insufficient credits")

    # Generate script using AI
    script_data = text_to_script.generate_script(
        movie_idea.title,
        movie_idea.genre,
        movie_idea.description
    )

    # Create movie record
    db_movie = models.Movie(
        user_id=current_user.id,
        title=movie_idea.title,
        genre=movie_idea.genre,
        style=movie_idea.style,
        description=movie_idea.description,
        script=script_data["script"],
        status="generating"
    )
    db.add(db_movie)
    db.flush()

    # Create scenes
    for scene_data in script_data["script"]:
        db_scene = models.Scene(
            movie_id=db_movie.id,
            scene_number=scene_data["scene_number"],
            description=scene_data["description"],
            status="generating"
        )
        db.add(db_scene)

        # Start async scene generation
        generate_movie_scene.delay(db_scene.id)

    db.commit()
    db.refresh(db_movie)

    return db_movie

@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Get movie details"""
    movie = db.query(models.Movie).filter(
        models.Movie.id == movie_id,
        models.Movie.user_id == current_user.id
    ).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return movie

@router.get("/{movie_id}/scenes", response_model=List[SceneResponse])
def get_movie_scenes(movie_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Get all scenes for a movie"""
    movie = db.query(models.Movie).filter(
        models.Movie.id == movie_id,
        models.Movie.user_id == current_user.id
    ).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    scenes = db.query(models.Scene).filter(models.Scene.movie_id == movie_id).order_by(models.Scene.scene_number).all()
    return scenes

@router.post("/scene/{scene_id}/update")
def update_scene(scene_id: int, update: SceneUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Update scene (accept/regenerate)"""
    scene = db.query(models.Scene).join(models.Movie).filter(
        models.Scene.id == scene_id,
        models.Movie.user_id == current_user.id
    ).first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if update.action == "regenerate":
        scene.status = "generating"
        scene.storyboard_url = None
        scene.video_url = None
        generate_movie_scene.delay(scene_id)
    elif update.action == "accept":
        scene.status = "completed"

    db.commit()
    return {"message": f"Scene {update.action}ed successfully"}

@router.post("/{movie_id}/generate-poster")
def generate_poster_endpoint(movie_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Generate movie poster"""
    movie = db.query(models.Movie).filter(
        models.Movie.id == movie_id,
        models.Movie.user_id == current_user.id
    ).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Generate poster
    poster_url = poster.generate_poster(movie.title, movie.genre)
    movie.poster_url = poster_url

    # Start async poster generation task
    generate_movie_poster.delay(movie_id)

    db.commit()
    return {"message": "Poster generation started"}

@router.post("/{movie_id}/generate-trailer")
def generate_trailer_endpoint(movie_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Generate movie trailer"""
    movie = db.query(models.Movie).filter(
        models.Movie.id == movie_id,
        models.Movie.user_id == current_user.id
    ).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Start async trailer generation
    generate_movie_trailer.delay(movie_id)

    return {"message": "Trailer generation started"}

@router.post("/{movie_id}/finalize")
def finalize_movie(movie_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Finalize movie - combine scenes and generate final video"""
    movie = db.query(models.Movie).filter(
        models.Movie.id == movie_id,
        models.Movie.user_id == current_user.id
    ).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if all scenes are completed
    scenes = db.query(models.Scene).filter(models.Scene.movie_id == movie_id).all()
    if not all(scene.status == "completed" for scene in scenes):
        raise HTTPException(status_code=400, detail="Not all scenes are completed")

    # Deduct credits
    user_credits = db.query(models.UserCredit).filter(models.UserCredit.user_id == current_user.id).first()
    total_credits_used = sum(scene.credits_used for scene in scenes)
    user_credits.credits -= total_credits_used

    # Start final movie generation
    generate_full_movie.delay(movie_id)

    db.commit()
    return {"message": "Movie finalization started", "credits_used": total_credits_used}

@router.get("/")
def get_user_movies(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Get all movies for current user"""
    movies = db.query(models.Movie).filter(models.Movie.user_id == current_user.id).order_by(models.Movie.created_at.desc()).all()
    return movies
