from celery import shared_task
from sqlalchemy.orm import Session
from . import database_models as models  

# AI generation functions
from models.ai_models import text_to_script, storyboard, video_gen, lip_sync, audio, poster, sound_effects


@shared_task
def generate_movie_scene(scene_id: int):
    """Generate a single movie scene"""
    db: Session = next(database.get_db())

    try:
        scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
        if not scene:
            return {"error": "Scene not found"}

        # Get movie (needed for genre, credits, etc.)
        movie = db.query(models.Movie).filter(models.Movie.id == scene.movie_id).first()
        if not movie:
            return {"error": "Movie not found"}

        # Generate storyboard
        storyboard_url = video_gen.generate_storyboard(scene.description, "cinematic")

        # Generate video from storyboard
        video_url = video_gen.generate_video(scene.description, storyboard_url)

        # Generate audio for the scene
        audio_url = audio.generate_audio(scene.description, "default")

        # Generate scene-specific music
        scene_music = audio.generate_scene_music(
            scene.description,
            movie.genre,
            scene.scene_number
        )

        # Store generated data
        scene.storyboard_url = storyboard_url
        scene.video_url = video_url
        scene.audio_url = audio_url
        scene.scene_music = scene_music
        scene.credits_used = 15
        scene.status = "completed"

        db.commit()

        return {"scene_id": scene_id, "status": "completed"}

    except Exception as e:
        if scene:
            scene.status = "failed"
            db.commit()
        return {"error": str(e)}


@shared_task
def generate_movie_poster(movie_id: int):
    """Generate movie poster"""
    db: Session = next(database.get_db())

    try:
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            return {"error": "Movie not found"}

        # Generate poster using AI
        poster_url = poster.generate_poster(movie.title, movie.genre)

        # Update movie with poster
        movie.poster_url = poster_url
        db.commit()

        return {"movie_id": movie_id, "status": "completed"}

    except Exception as e:
        return {"error": str(e)}


@shared_task
def generate_movie_trailer(movie_id: int):
    """Generate movie trailer"""
    db: Session = next(database.get_db())

    try:
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            return {"error": "Movie not found"}

        # Get all completed scenes
        scenes = db.query(models.Scene).filter(
            models.Scene.movie_id == movie_id,
            models.Scene.status == "completed"
        ).order_by(models.Scene.scene_number).limit(3).all()

        if scenes:
            # Collect data for trailer
            scenes_data = [
                {
                    "title": f"Scene {scene.scene_number}",
                    "description": scene.description,
                    "storyboard_url": scene.storyboard_url,
                    "video_url": scene.video_url,
                    "audio_url": scene.audio_url,
                }
                for scene in scenes
            ]

            # Generate trailer video
            trailer_path = video_gen.generate_multi_scene_video(scenes_data)
            movie.trailer_url = trailer_path

        # Fallback if no trailer created
        if not movie.trailer_url:
            movie.trailer_url = f"https://example.com/trailer_{movie_id}.mp4"

        db.commit()
        return {"movie_id": movie_id, "status": "completed"}

    except Exception as e:
        return {"error": str(e)}


@shared_task
def generate_full_movie(movie_id: int):
    """Generate full movie by combining all scenes"""
    db: Session = next(database.get_db())

    try:
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if not movie:
            return {"error": "Movie not found"}

        print(f"🎬 Starting full movie generation for: {movie.title}")

        # Get all completed scenes
        scenes = db.query(models.Scene).filter(
            models.Scene.movie_id == movie_id,
            models.Scene.status == "completed"
        ).order_by(models.Scene.scene_number).all()

        if not scenes:
            return {"error": "No completed scenes found"}

        # Prepare data for video generation
        scenes_data = [
            {
                "title": f"Scene {scene.scene_number}",
                "description": scene.description,
                "storyboard_url": scene.storyboard_url,
                "video_url": scene.video_url,
                "audio_url": scene.audio_url,
                "sound_effects": scene.sound_effects,
                "scene_music": scene.scene_music,
            }
            for scene in scenes
        ]

        print(f"📹 Processing {len(scenes_data)} scenes...")

        # Generate multi-scene video with audio
        final_video_path = video_gen.generate_multi_scene_video_with_audio(scenes_data)

        # Generate final poster
        poster_url = poster.generate_poster(movie.title, movie.genre)

        # Calculate credits
        total_credits = sum(scene.credits_used for scene in scenes) + 50  # +50 final compilation

        # Update movie record
        movie.video_url = final_video_path
        movie.poster_url = poster_url
        movie.status = "completed"
        movie.credits_used = total_credits

        # Deduct credits from user
        user_credits = db.query(models.UserCredit).filter(
            models.UserCredit.user_id == movie.user_id
        ).first()
        if user_credits:
            user_credits.credits -= total_credits

        db.commit()

        print("✅ Full movie generation completed successfully!")
        return {
            "movie_id": movie_id,
            "status": "completed",
            "video_url": final_video_path,
            "credits_used": total_credits,
        }

    except Exception as e:
        print(f"❌ Error in full movie generation: {e}")
        if movie:
            movie.status = "failed"
            db.commit()

        return {"error": str(e)}
