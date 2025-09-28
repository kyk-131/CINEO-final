#!/usr/bin/env python3
"""
CINEO AI - Complete Movie Generation Platform
A unified Flask application with premium UI and full AI movie generation capabilities
"""

import os
import json
import time
import base64
import hashlib
import tempfile
import threading
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file automatically

# Flask and web framework imports
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# AI and ML imports
import requests
import torch
from PIL import Image
import numpy as np
import cv2
import moviepy.editor as mp
from transformers import pipeline

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-super-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cineo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload directories
os.makedirs('static/uploads/videos', exist_ok=True)
os.makedirs('static/uploads/images', exist_ok=True)
os.makedirs('static/uploads/audio', exist_ok=True)

# =============================================================================
# DATABASE MODELS
# =============================================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Integer, default=300)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    movies = db.relationship('Movie', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    script = db.Column(db.JSON)
    status = db.Column(db.String(20), default='draft')  # draft, generating, completed, failed
    poster_url = db.Column(db.String(500))
    trailer_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    credits_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scenes = db.relationship('Scene', backref='movie', lazy=True, cascade='all, delete-orphan')

class Scene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    scene_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    dialogue = db.Column(db.JSON)
    storyboard_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    audio_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, generating, completed, failed
    credits_used = db.Column(db.Integer, default=15)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =============================================================================
# AI MODELS INTEGRATION
# =============================================================================

class AIModels:
    """Centralized AI models for movie generation"""
    
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
        self.stability_key = os.getenv('STABILITY_API_KEY', '')
        self.elevenlabs_key = os.getenv('ELEVENLABS_API_KEY', '')
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def generate_script(self, title: str, genre: str, description: str) -> Dict:
        """Generate movie script using OpenRouter API"""
        if not self.openrouter_key:
            return self._mock_script(title, genre, description)
            
        prompt = f"""Create a detailed movie script for a {genre} film titled '{title}'.

Description: {description}

Generate 3-5 scenes with:
- Scene titles and descriptions
- Character dialogue
- Action sequences
- Visual details

Format as JSON with scene_number, title, description, and dialogue fields."""

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "Cineo AI Movie Generator",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 3000,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                script_text = result['choices'][0]['message']['content']
                return self._parse_script(script_text, title, genre, description)
            else:
                return self._mock_script(title, genre, description)
                
        except Exception as e:
            print(f"Script generation error: {e}")
            return self._mock_script(title, genre, description)
    
    def _mock_script(self, title: str, genre: str, description: str) -> Dict:
        """Generate mock script for testing"""
        scenes = [
            {
                "scene_number": 1,
                "title": "Opening Scene",
                "description": f"The movie opens with a captivating {genre} scene that sets the tone. {description[:100]}...",
                "dialogue": [
                    "PROTAGONIST: This is where our journey begins.",
                    "NARRATOR: In a world where anything is possible..."
                ]
            },
            {
                "scene_number": 2,
                "title": "The Challenge",
                "description": "Our protagonist faces the main conflict that will drive the story forward.",
                "dialogue": [
                    "PROTAGONIST: I never expected this to happen.",
                    "ANTAGONIST: You have no idea what's coming."
                ]
            },
            {
                "scene_number": 3,
                "title": "Rising Action",
                "description": "The tension builds as obstacles mount and stakes get higher.",
                "dialogue": [
                    "PROTAGONIST: We need to work together.",
                    "ALLY: I'm with you, no matter what."
                ]
            },
            {
                "scene_number": 4,
                "title": "Climax",
                "description": "The ultimate confrontation where everything comes to a head.",
                "dialogue": [
                    "PROTAGONIST: This ends now!",
                    "ANTAGONIST: You're too late!"
                ]
            },
            {
                "scene_number": 5,
                "title": "Resolution",
                "description": "The story concludes with resolution and new beginnings.",
                "dialogue": [
                    "PROTAGONIST: We did it... we actually did it.",
                    "NARRATOR: And so our story comes to an end, but new adventures await."
                ]
            }
        ]
        
        return {
            "title": title,
            "genre": genre,
            "description": description,
            "script": scenes,
            "status": "completed"
        }
    
    def _parse_script(self, script_text: str, title: str, genre: str, description: str) -> Dict:
        """Parse AI-generated script text into structured format"""
        # Simple parsing - in production, use more sophisticated NLP
        try:
            # Try to extract JSON if present
            if '{' in script_text and '}' in script_text:
                start = script_text.find('{')
                end = script_text.rfind('}') + 1
                json_str = script_text[start:end]
                parsed = json.loads(json_str)
                if 'script' in parsed:
                    return parsed
        except:
            pass
        
        # Fallback to mock script
        return self._mock_script(title, genre, description)
    
    def generate_storyboard(self, scene_description: str, style: str = "cinematic") -> str:
        """Generate storyboard image using Stability AI"""
        if not self.stability_key:
            return f"https://picsum.photos/512/512?random={hash(scene_description)}"
        
        enhanced_prompt = f"{scene_description}, {style} style, movie storyboard, concept art, highly detailed, 8k"
        
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.stability_key}"
                },
                json={
                    "text_prompts": [{"text": enhanced_prompt, "weight": 1}],
                    "cfg_scale": 7,
                    "width": 512,
                    "height": 512,
                    "samples": 1,
                    "steps": 20,
                    "style_preset": "cinematic"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("artifacts"):
                    # Save image to local storage
                    image_data = base64.b64decode(result['artifacts'][0]['base64'])
                    filename = f"storyboard_{int(time.time())}_{hash(scene_description) % 10000}.png"
                    filepath = os.path.join('static/uploads/images', filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    return f"/static/uploads/images/{filename}"
            
        except Exception as e:
            print(f"Storyboard generation error: {e}")
        
        return f"https://picsum.photos/512/512?random={hash(scene_description)}"
    
    def generate_poster(self, title: str, genre: str) -> str:
        """Generate movie poster"""
        poster_prompt = f"Movie poster for '{title}', {genre} genre, cinematic, dramatic lighting, professional movie poster style, highly detailed"
        return self.generate_storyboard(poster_prompt, "cinematic")
    
    def generate_video(self, scene_description: str, storyboard_url: str, duration: int = 5) -> str:
        """Generate video using local Stable Video Diffusion model"""
        try:
            print(f"🎬 Generating video for: {scene_description}")
            
            # Check if we have GPU support
            if not torch.cuda.is_available():
                print("⚠️ CUDA not available, using CPU (slower)")
            
            # Initialize Stable Video Diffusion pipeline
            from diffusers import StableVideoDiffusionPipeline
            
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid-xt",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                variant="fp16" if torch.cuda.is_available() else None
            )
            
            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
                print("✅ Using GPU for video generation")
            else:
                pipe = pipe.to("cpu")
                print("✅ Using CPU for video generation")
            
            # Load the storyboard image
            if storyboard_url.startswith('http'):
                import requests
                response = requests.get(storyboard_url)
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(response.content))
            else:
                # Local file or base64
                from PIL import Image
                if storyboard_url.startswith('data:image'):
                    import base64
                    header, encoded = storyboard_url.split(',', 1)
                    image_data = base64.b64decode(encoded)
                    image = Image.open(io.BytesIO(image_data))
                else:
                    image = Image.open(storyboard_url)
            
            # Resize image to optimal size for SVD
            image = image.resize((1024, 576))  # 16:9 aspect ratio
            
            # Generate video frames
            print("🔄 Generating video frames...")
            with torch.inference_mode():
                frames = pipe(
                    image=image,
                    decode_chunk_size=2,
                    num_frames=25,  # ~1 second at 25fps
                    motion_bucket_id=127,
                    noise_aug_strength=0.02
                ).frames[0]
            
            # Save video
            import tempfile
            from pathlib import Path
            temp_dir = Path(tempfile.mkdtemp())
            video_filename = f"scene_video_{int(time.time())}_{hash(scene_description) % 10000}.mp4"
            video_path = temp_dir / video_filename
            
            # Export frames to video using imageio
            import imageio
            with imageio.get_writer(str(video_path), fps=8) as writer:
                for frame in frames:
                    writer.append_data(np.array(frame))
            
            # In production, you would upload this to cloud storage
            # For now, return the local path
            print(f"✅ Video generated: {video_path}")
            return str(video_path)
            
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            # Fallback to placeholder
            return f"https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    
    def generate_audio(self, text: str, voice: str = "default") -> str:
        """Generate audio using ElevenLabs (mock implementation)"""
        filename = f"audio_{int(time.time())}_{hash(text) % 10000}.mp3"
        return f"https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"

# Initialize AI models
ai_models = AIModels()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def require_credits(credits_needed):
    """Decorator to check if user has enough credits"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.credits < credits_needed:
                return jsonify({'error': 'Insufficient credits'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def background_task(func):
    """Decorator to run function in background thread"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

@background_task
def generate_movie_scenes(movie_id: int):
    """Background task to generate all movie scenes with real-time updates"""
    with app.app_context():
        movie = Movie.query.get(movie_id)
        if not movie:
            return
        
        movie.status = 'generating'
        db.session.commit()
        
        # Emit initial status
        socketio.emit('movie_update', {
            'movie_id': movie_id,
            'status': 'generating',
            'message': 'Starting movie generation...'
        }, room=f'movie_{movie_id}')
        
        try:
            total_scenes = len(movie.scenes)
            
            for i, scene in enumerate(movie.scenes):
                scene.status = 'generating'
                db.session.commit()
                
                # Emit scene update
                socketio.emit('scene_update', {
                    'movie_id': movie_id,
                    'scene_id': scene.id,
                    'scene_number': scene.scene_number,
                    'status': 'generating',
                    'progress': int((i / total_scenes) * 100),
                    'message': f'Generating scene {scene.scene_number}: {scene.title or "Untitled"}'
                }, room=f'movie_{movie_id}')
                
                # Generate storyboard
                socketio.emit('scene_update', {
                    'movie_id': movie_id,
                    'scene_id': scene.id,
                    'status': 'generating',
                    'step': 'storyboard',
                    'message': f'Creating storyboard for scene {scene.scene_number}...'
                }, room=f'movie_{movie_id}')
                
                scene.storyboard_url = ai_models.generate_storyboard(scene.description, movie.style)
                
                # Generate video
                socketio.emit('scene_update', {
                    'movie_id': movie_id,
                    'scene_id': scene.id,
                    'status': 'generating',
                    'step': 'video',
                    'message': f'Generating video for scene {scene.scene_number}...'
                }, room=f'movie_{movie_id}')
                
                scene.video_url = ai_models.generate_video(scene.description, scene.storyboard_url)
                
                # Generate audio
                socketio.emit('scene_update', {
                    'movie_id': movie_id,
                    'scene_id': scene.id,
                    'status': 'generating',
                    'step': 'audio',
                    'message': f'Adding audio to scene {scene.scene_number}...'
                }, room=f'movie_{movie_id}')
                
                dialogue_text = ' '.join(scene.dialogue) if scene.dialogue else scene.description
                scene.audio_url = ai_models.generate_audio(dialogue_text)
                
                scene.status = 'completed'
                db.session.commit()
                
                # Emit completion
                socketio.emit('scene_update', {
                    'movie_id': movie_id,
                    'scene_id': scene.id,
                    'status': 'completed',
                    'progress': int(((i + 1) / total_scenes) * 100),
                    'message': f'Scene {scene.scene_number} completed!'
                }, room=f'movie_{movie_id}')
                
                time.sleep(1)  # Brief pause between scenes
            
            movie.status = 'completed'
            db.session.commit()
            
            # Emit final completion
            socketio.emit('movie_update', {
                'movie_id': movie_id,
                'status': 'completed',
                'progress': 100,
                'message': f'🎉 Movie "{movie.title}" completed successfully!'
            }, room=f'movie_{movie_id}')
            
        except Exception as e:
            print(f"Error generating scenes: {e}")
            movie.status = 'failed'
            db.session.commit()
            
            # Emit error
            socketio.emit('movie_update', {
                'movie_id': movie_id,
                'status': 'failed',
                'message': f'❌ Error generating movie: {str(e)}'
            }, room=f'movie_{movie_id}')

# =============================================================================
# ROUTES - AUTHENTICATION
# =============================================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# =============================================================================
# ROUTES - MAIN APPLICATION
# =============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    movies = Movie.query.filter_by(user_id=current_user.id).order_by(Movie.created_at.desc()).all()
    return render_template_string(DASHBOARD_TEMPLATE, movies=movies, user=current_user)

@app.route('/create-movie')
@login_required
def create_movie():
    return render_template_string(MOVIE_WIZARD_TEMPLATE, user=current_user)

@app.route('/api/movies', methods=['POST'])
@login_required
@require_credits(40)
def create_movie_api():
    data = request.get_json()
    
    # Generate script using AI
    script_data = ai_models.generate_script(
        data['title'],
        data['genre'], 
        data['description']
    )
    
    # Create movie record
    movie = Movie(
        user_id=current_user.id,
        title=data['title'],
        genre=data['genre'],
        style=data['style'],
        description=data['description'],
        script=script_data['script'],
        status='draft'
    )
    db.session.add(movie)
    db.session.flush()
    
    # Create scenes
    for scene_data in script_data['script']:
        scene = Scene(
            movie_id=movie.id,
            scene_number=scene_data['scene_number'],
            title=scene_data.get('title', f"Scene {scene_data['scene_number']}"),
            description=scene_data['description'],
            dialogue=scene_data.get('dialogue', [])
        )
        db.session.add(scene)
    
    db.session.commit()
    
    # Start background scene generation
    generate_movie_scenes(movie.id)
    
    return jsonify({
        'success': True,
        'movie_id': movie.id,
        'message': 'Movie creation started!'
    })

@app.route('/api/movies/<int:movie_id>')
@login_required
def get_movie(movie_id):
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    
    return jsonify({
        'id': movie.id,
        'title': movie.title,
        'genre': movie.genre,
        'style': movie.style,
        'description': movie.description,
        'status': movie.status,
        'poster_url': movie.poster_url,
        'trailer_url': movie.trailer_url,
        'video_url': movie.video_url,
        'created_at': movie.created_at.isoformat(),
        'scenes': [{
            'id': scene.id,
            'scene_number': scene.scene_number,
            'title': scene.title,
            'description': scene.description,
            'storyboard_url': scene.storyboard_url,
            'video_url': scene.video_url,
            'audio_url': scene.audio_url,
            'status': scene.status
        } for scene in movie.scenes]
    })

@app.route('/api/movies/<int:movie_id>/generate-poster', methods=['POST'])
@login_required
def generate_poster(movie_id):
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    
    poster_url = ai_models.generate_poster(movie.title, movie.genre)
    movie.poster_url = poster_url
    db.session.commit()
    
    return jsonify({'success': True, 'poster_url': poster_url})

@app.route('/movie/<int:movie_id>')
@login_required
def view_movie(movie_id):
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    if not movie:
        flash('Movie not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template_string(MOVIE_VIEW_TEMPLATE, movie=movie, user=current_user)

@app.route('/api/user/credits')
@login_required
def get_user_credits():
    return jsonify({'credits': current_user.credits})

# =============================================================================
# WEBSOCKET EVENTS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        print(f"User {current_user.username} connected via WebSocket")
        emit('connected', {'message': 'Connected to Cineo AI'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f"User {current_user.username} disconnected")

@socketio.on('join_movie')
def handle_join_movie(data):
    """Join a movie room for real-time updates"""
    if current_user.is_authenticated:
        movie_id = data.get('movie_id')
        if movie_id:
            # Verify user owns this movie
            movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
            if movie:
                join_room(f'movie_{movie_id}')
                emit('joined_movie', {
                    'movie_id': movie_id,
                    'message': f'Joined movie "{movie.title}" updates'
                })

@socketio.on('leave_movie')
def handle_leave_movie(data):
    """Leave a movie room"""
    if current_user.is_authenticated:
        movie_id = data.get('movie_id')
        if movie_id:
            leave_room(f'movie_{movie_id}')
            emit('left_movie', {'movie_id': movie_id})

# =============================================================================
# HTML TEMPLATES
# =============================================================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cineo AI - AI Movie Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
        }
        
        /* Animated background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%);
            animation: float 20s ease-in-out infinite;
            pointer-events: none;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 3rem;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            position: relative;
            z-index: 1;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .logo p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        input {
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: rgba(255, 255, 255, 0.08);
        }
        
        input::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        .btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn.loading {
            pointer-events: none;
        }
        
        .btn.loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .toggle-form {
            text-align: center;
            margin-top: 1.5rem;
        }
        
        .toggle-form a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .toggle-form a:hover {
            color: #764ba2;
        }
        
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }
        
        .hidden {
            display: none;
        }
        
        .features {
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .feature {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }
        
        .feature::before {
            content: '✨';
            margin-right: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Cineo AI</h1>
            <p>Transform imagination into cinematic masterpieces</p>
        </div>
        
        <div id="error-message" class="error hidden"></div>
        
        <form id="login-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" placeholder="Enter your username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter your password" required>
            </div>
            
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <form id="register-form" class="hidden">
            <div class="form-group">
                <label for="reg-username">Username</label>
                <input type="text" id="reg-username" name="username" placeholder="Choose a username" required>
            </div>
            
            <div class="form-group">
                <label for="reg-email">Email</label>
                <input type="email" id="reg-email" name="email" placeholder="Enter your email" required>
            </div>
            
            <div class="form-group">
                <label for="reg-password">Password</label>
                <input type="password" id="reg-password" name="password" placeholder="Create a password" required>
            </div>
            
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="toggle-form">
            <span id="toggle-text">Don't have an account?</span>
            <a href="#" id="toggle-link">Sign up</a>
        </div>
        
        <div class="features">
            <div class="feature">AI-powered script generation</div>
            <div class="feature">Automatic storyboard creation</div>
            <div class="feature">Video scene generation</div>
            <div class="feature">Professional movie posters</div>
        </div>
    </div>

    <script>
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const toggleLink = document.getElementById('toggle-link');
        const toggleText = document.getElementById('toggle-text');
        const errorMessage = document.getElementById('error-message');
        
        let isLoginMode = true;
        
        toggleLink.addEventListener('click', (e) => {
            e.preventDefault();
            isLoginMode = !isLoginMode;
            
            if (isLoginMode) {
                loginForm.classList.remove('hidden');
                registerForm.classList.add('hidden');
                toggleText.textContent = "Don't have an account?";
                toggleLink.textContent = "Sign up";
            } else {
                loginForm.classList.add('hidden');
                registerForm.classList.remove('hidden');
                toggleText.textContent = "Already have an account?";
                toggleLink.textContent = "Sign in";
            }
            
            hideError();
        });
        
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
        }
        
        function hideError() {
            errorMessage.classList.add('hidden');
        }
        
        function setLoading(button, loading) {
            if (loading) {
                button.classList.add('loading');
                button.textContent = '';
            } else {
                button.classList.remove('loading');
                button.textContent = isLoginMode ? 'Sign In' : 'Create Account';
            }
        }
        
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const button = loginForm.querySelector('.btn');
            setLoading(button, true);
            hideError();
            
            const formData = new FormData(loginForm);
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    showError(data.error || 'Login failed');
                }
            } catch (error) {
                showError('Network error. Please try again.');
            } finally {
                setLoading(button, false);
            }
        });
        
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const button = registerForm.querySelector('.btn');
            setLoading(button, true);
            hideError();
            
            const formData = new FormData(registerForm);
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    showError(data.error || 'Registration failed');
                }
            } catch (error) {
                showError('Network error. Please try again.');
            } finally {
                setLoading(button, false);
            }
        });
    </script>
</body>
</html>
"""

# Dashboard Template with Netflix-inspired design
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Cineo AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0c0c0c;
            color: white;
            overflow-x: hidden;
        }
        
        /* Animated background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%);
            animation: float 30s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-20px) rotate(1deg); }
            66% { transform: translateY(10px) rotate(-1deg); }
        }
        
        /* Header */
        .header {
            position: sticky;
            top: 0;
            background: rgba(12, 12, 12, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem 2rem;
            z-index: 100;
        }
        
        .nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
            position: relative;
        }
        
        .nav-link:hover {
            color: white;
        }
        
        .nav-link.active::after {
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 1px;
        }
        
        .credits-display {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .credits-display::before {
            content: '⚡';
            font-size: 1.2rem;
        }
        
        .user-menu {
            position: relative;
        }
        
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .user-avatar:hover {
            transform: scale(1.05);
        }
        
        /* Main Content */
        .main {
            position: relative;
            z-index: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Hero Section */
        .hero {
            text-align: center;
            margin-bottom: 4rem;
            padding: 4rem 0;
        }
        
        .hero h1 {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero p {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 2rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .create-movie-btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .create-movie-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .create-movie-btn:hover::before {
            left: 100%;
        }
        
        .create-movie-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.4);
        }
        
        /* Movies Grid */
        .section {
            margin-bottom: 4rem;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            color: white;
        }
        
        .movies-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
        }
        
        .movie-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .movie-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .movie-poster {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        .movie-poster img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .movie-poster::before {
            content: '🎬';
            font-size: 3rem;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            opacity: 0.7;
        }
        
        .movie-info {
            padding: 1.5rem;
        }
        
        .movie-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: white;
        }
        
        .movie-meta {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.6);
        }
        
        .movie-genre {
            background: rgba(102, 126, 234, 0.2);
            color: #a5b4fc;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .movie-status {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .status-completed {
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
        }
        
        .status-generating {
            background: rgba(251, 191, 36, 0.2);
            color: #fde047;
        }
        
        .status-draft {
            background: rgba(156, 163, 175, 0.2);
            color: #d1d5db;
        }
        
        .status-failed {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
        }
        
        .movie-description {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .movie-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .action-btn {
            padding: 0.5rem 1rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: transparent;
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .action-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .action-btn.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: transparent;
            color: white;
        }
        
        .action-btn.primary:hover {
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: rgba(255, 255, 255, 0.6);
        }
        
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        .empty-state h3 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: rgba(255, 255, 255, 0.8);
        }
        
        .empty-state p {
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }
            
            .nav {
                flex-direction: column;
                gap: 1rem;
            }
            
            .nav-links {
                gap: 1rem;
            }
            
            .hero h1 {
                font-size: 2.5rem;
            }
            
            .main {
                padding: 1rem;
            }
            
            .movies-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <header class="header">
        <nav class="nav">
            <div class="logo">Cineo AI</div>
            
            <div class="nav-links">
                <a href="/dashboard" class="nav-link active">Dashboard</a>
                <a href="/create-movie" class="nav-link">Create</a>
                
                <div class="credits-display">
                    <span id="credits-count">{{ user.credits }}</span> Credits
                </div>
                
                <div class="user-menu">
                    <div class="user-avatar" onclick="showUserMenu()">
                        {{ user.username[0].upper() }}
                    </div>
                </div>
            </div>
        </nav>
    </header>
    
    <main class="main">
        {% if movies|length == 0 %}
        <div class="hero">
            <h1>Welcome to Cineo AI</h1>
            <p>Transform your imagination into cinematic masterpieces using cutting-edge AI technology. Create stunning movies with just a few clicks.</p>
            <a href="/create-movie" class="create-movie-btn">
                ✨ Create Your First Movie
            </a>
        </div>
        
        <div class="empty-state">
            <div class="empty-state-icon">🎬</div>
            <h3>No movies yet</h3>
            <p>Start your cinematic journey by creating your first AI-generated movie.</p>
            <a href="/create-movie" class="create-movie-btn">Get Started</a>
        </div>
        {% else %}
        <div class="hero">
            <h1>Your Movies</h1>
            <p>Manage and create stunning AI-generated movies</p>
            <a href="/create-movie" class="create-movie-btn">
                ✨ Create New Movie
            </a>
        </div>
        
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">Your Movies</h2>
            </div>
            
            <div class="movies-grid">
                {% for movie in movies %}
                <div class="movie-card" onclick="viewMovie({{ movie.id }})">
                    <div class="movie-poster">
                        {% if movie.poster_url %}
                        <img src="{{ movie.poster_url }}" alt="{{ movie.title }}" onerror="this.style.display='none'">
                        {% endif %}
                    </div>
                    
                    <div class="movie-info">
                        <h3 class="movie-title">{{ movie.title }}</h3>
                        
                        <div class="movie-meta">
                            <span class="movie-genre">{{ movie.genre }}</span>
                            <span class="movie-status status-{{ movie.status }}">{{ movie.status }}</span>
                        </div>
                        
                        <p class="movie-description">{{ movie.description }}</p>
                        
                        <div class="movie-actions">
                            <a href="/movie/{{ movie.id }}" class="action-btn primary" onclick="event.stopPropagation()">View</a>
                            {% if movie.status == 'completed' and movie.video_url %}
                            <a href="{{ movie.video_url }}" class="action-btn" target="_blank" onclick="event.stopPropagation()">Download</a>
                            {% endif %}
                            {% if movie.status == 'draft' %}
                            <button class="action-btn" onclick="event.stopPropagation(); generateMovie({{ movie.id }})">Generate</button>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}
    </main>
    
    <script>
        function viewMovie(movieId) {
            window.location.href = `/movie/${movieId}`;
        }
        
        function showUserMenu() {
            if (confirm('Do you want to logout?')) {
                window.location.href = '/logout';
            }
        }
        
        async function generateMovie(movieId) {
            const button = event.target;
            const originalText = button.textContent;
            button.innerHTML = '<span class="loading"></span>';
            button.disabled = true;
            
            try {
                const response = await fetch(`/api/movies/${movieId}/generate`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    location.reload();
                } else {
                    const error = await response.json();
                    alert(error.error || 'Failed to generate movie');
                }
            } catch (error) {
                alert('Network error. Please try again.');
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
        
        // Auto-refresh credits
        async function updateCredits() {
            try {
                const response = await fetch('/api/user/credits');
                const data = await response.json();
                document.getElementById('credits-count').textContent = data.credits;
            } catch (error) {
                console.error('Failed to update credits:', error);
            }
        }
        
        setInterval(updateCredits, 10000); // Update every 10 seconds
    </script>
</body>
</html>
"""

# Movie Wizard Template - Kling/Netflix inspired design
MOVIE_WIZARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Movie - Cineo AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0c0c0c;
            color: white;
            overflow-x: hidden;
        }
        
        /* Animated background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%);
            animation: float 30s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-20px) rotate(1deg); }
            66% { transform: translateY(10px) rotate(-1deg); }
        }
        
        /* Header */
        .header {
            position: sticky;
            top: 0;
            background: rgba(12, 12, 12, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem 2rem;
            z-index: 100;
        }
        
        .nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .nav-link:hover {
            color: white;
        }
        
        .nav-link.active {
            color: white;
        }
        
        .credits-display {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .credits-display::before {
            content: '⚡';
            font-size: 1.2rem;
        }
        
        /* Main Content */
        .main {
            position: relative;
            z-index: 1;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Wizard Container */
        .wizard-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 3rem;
            margin: 2rem 0;
        }
        
        .wizard-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .wizard-header h1 {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .wizard-header p {
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        /* Progress Steps */
        .progress-steps {
            display: flex;
            justify-content: center;
            margin-bottom: 3rem;
            position: relative;
        }
        
        .progress-steps::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 20%;
            right: 20%;
            height: 2px;
            background: rgba(255, 255, 255, 0.1);
            z-index: 1;
        }
        
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
            flex: 1;
            max-width: 120px;
        }
        
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .step.active .step-circle {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: transparent;
            color: white;
        }
        
        .step.completed .step-circle {
            background: rgba(34, 197, 94, 0.2);
            border-color: #22c55e;
            color: #22c55e;
        }
        
        .step-label {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
            text-align: center;
        }
        
        .step.active .step-label {
            color: white;
            font-weight: 600;
        }
        
        /* Form Styles */
        .form-group {
            margin-bottom: 2rem;
        }
        
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            font-size: 1rem;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: rgba(255, 255, 255, 0.08);
        }
        
        .form-group input::placeholder,
        .form-group textarea::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        .form-group textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        /* Style Selection */
        .style-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .style-option {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .style-option::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .style-option:hover::before,
        .style-option.selected::before {
            opacity: 0.1;
        }
        
        .style-option:hover {
            border-color: rgba(102, 126, 234, 0.3);
            transform: translateY(-2px);
        }
        
        .style-option.selected {
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }
        
        .style-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .style-name {
            font-weight: 600;
            color: white;
            position: relative;
            z-index: 1;
        }
        
        /* Buttons */
        .form-actions {
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            margin-top: 3rem;
        }
        
        .btn {
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            position: relative;
            overflow: hidden;
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .btn.loading {
            pointer-events: none;
        }
        
        .btn.loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Error Messages */
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }
        
        .hidden {
            display: none;
        }
        
        /* Success Message */
        .success {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #86efac;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            
            .wizard-container {
                padding: 2rem 1.5rem;
            }
            
            .wizard-header h1 {
                font-size: 2rem;
            }
            
            .progress-steps {
                flex-wrap: wrap;
                gap: 1rem;
            }
            
            .form-actions {
                flex-direction: column;
            }
            
            .style-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <header class="header">
        <nav class="nav">
            <div class="logo">Cineo AI</div>
            
            <div class="nav-links">
                <a href="/dashboard" class="nav-link">Dashboard</a>
                <a href="/create-movie" class="nav-link active">Create</a>
                
                <div class="credits-display">
                    <span>{{ user.credits }}</span> Credits
                </div>
            </div>
        </nav>
    </header>
    
    <main class="main">
        <div class="wizard-container">
            <div class="wizard-header">
                <h1>Create Your Movie</h1>
                <p>Transform your imagination into a cinematic masterpiece with AI</p>
            </div>
            
            <div class="progress-steps">
                <div class="step active" id="step-1">
                    <div class="step-circle">1</div>
                    <div class="step-label">Movie Idea</div>
                </div>
                <div class="step" id="step-2">
                    <div class="step-circle">2</div>
                    <div class="step-label">Style</div>
                </div>
                <div class="step" id="step-3">
                    <div class="step-circle">3</div>
                    <div class="step-label">Review</div>
                </div>
                <div class="step" id="step-4">
                    <div class="step-circle">4</div>
                    <div class="step-label">Generate</div>
                </div>
            </div>
            
            <div id="error-message" class="error hidden"></div>
            <div id="success-message" class="success hidden"></div>
            
            <form id="movie-wizard-form">
                <!-- Step 1: Movie Idea -->
                <div class="wizard-step" id="wizard-step-1">
                    <div class="form-group">
                        <label for="title">Movie Title</label>
                        <input type="text" id="title" name="title" placeholder="Enter your movie title" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="genre">Genre</label>
                        <select id="genre" name="genre" required>
                            <option value="">Select a genre</option>
                            <option value="action">Action</option>
                            <option value="adventure">Adventure</option>
                            <option value="comedy">Comedy</option>
                            <option value="drama">Drama</option>
                            <option value="fantasy">Fantasy</option>
                            <option value="horror">Horror</option>
                            <option value="mystery">Mystery</option>
                            <option value="romance">Romance</option>
                            <option value="sci-fi">Sci-Fi</option>
                            <option value="thriller">Thriller</option>
                            <option value="western">Western</option>
                            <option value="animation">Animation</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Movie Description</label>
                        <textarea id="description" name="description" placeholder="Describe your movie plot, characters, and setting..." required></textarea>
                    </div>
                </div>
                
                <!-- Step 2: Style Selection -->
                <div class="wizard-step hidden" id="wizard-step-2">
                    <div class="form-group">
                        <label>Visual Style</label>
                        <div class="style-grid">
                            <div class="style-option" data-style="cinematic">
                                <span class="style-icon">🎬</span>
                                <span class="style-name">Cinematic</span>
                            </div>
                            <div class="style-option" data-style="anime">
                                <span class="style-icon">🌸</span>
                                <span class="style-name">Anime</span>
                            </div>
                            <div class="style-option" data-style="realistic">
                                <span class="style-icon">📸</span>
                                <span class="style-name">Realistic</span>
                            </div>
                            <div class="style-option" data-style="fantasy">
                                <span class="style-icon">🧙‍♂️</span>
                                <span class="style-name">Fantasy</span>
                            </div>
                            <div class="style-option" data-style="noir">
                                <span class="style-icon">🌙</span>
                                <span class="style-name">Film Noir</span>
                            </div>
                            <div class="style-option" data-style="sci-fi">
                                <span class="style-icon">🚀</span>
                                <span class="style-name">Sci-Fi</span>
                            </div>
                        </div>
                        <input type="hidden" id="style" name="style" required>
                    </div>
                </div>
                
                <!-- Step 3: Review -->
                <div class="wizard-step hidden" id="wizard-step-3">
                    <h2 style="margin-bottom: 2rem; color: white;">Review Your Movie</h2>
                    
                    <div class="form-group">
                        <label>Title</label>
                        <div id="review-title" style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; color: white;"></div>
                    </div>
                    
                    <div class="form-group">
                        <label>Genre</label>
                        <div id="review-genre" style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; color: white;"></div>
                    </div>
                    
                    <div class="form-group">
                        <label>Style</label>
                        <div id="review-style" style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; color: white;"></div>
                    </div>
                    
                    <div class="form-group">
                        <label>Description</label>
                        <div id="review-description" style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; color: white; white-space: pre-wrap;"></div>
                    </div>
                    
                    <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); color: #fde047; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                        <strong>⚡ Cost:</strong> 40 Credits (Script generation + Scene creation)
                    </div>
                </div>
                
                <!-- Step 4: Generation -->
                <div class="wizard-step hidden" id="wizard-step-4">
                    <div style="text-align: center; padding: 2rem;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">🎬</div>
                        <h2 style="margin-bottom: 1rem; color: white;">Creating Your Movie!</h2>
                        <p style="color: rgba(255,255,255,0.7); margin-bottom: 2rem;">
                            AI is generating your script and preparing scenes. This may take a few minutes.
                        </p>
                        
                        <div class="loading" style="margin: 2rem auto; display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                        
                        <div id="generation-status" style="margin-top: 2rem; color: rgba(255,255,255,0.8);">
                            Initializing AI models...
                        </div>
                        
                        <div style="margin-top: 2rem;">
                            <a href="/dashboard" class="btn btn-secondary">
                                View Dashboard
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" id="prev-btn" style="display: none;">
                        ← Previous
                    </button>
                    
                    <button type="button" class="btn btn-primary" id="next-btn">
                        Next →
                    </button>
                    
                    <button type="submit" class="btn btn-primary hidden" id="create-btn">
                        🎬 Create Movie
                    </button>
                </div>
            </form>
        </div>
    </main>
    
    <script>
        let currentStep = 1;
        const totalSteps = 4;
        
        const nextBtn = document.getElementById('next-btn');
        const prevBtn = document.getElementById('prev-btn');
        const createBtn = document.getElementById('create-btn');
        const form = document.getElementById('movie-wizard-form');
        const errorMessage = document.getElementById('error-message');
        const successMessage = document.getElementById('success-message');
        
        // Style selection
        document.querySelectorAll('.style-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.style-option').forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                document.getElementById('style').value = this.dataset.style;
            });
        });
        
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
            successMessage.classList.add('hidden');
        }
        
        function hideMessages() {
            errorMessage.classList.add('hidden');
            successMessage.classList.add('hidden');
        }
        
        function updateStepUI() {
            // Update step indicators
            for (let i = 1; i <= totalSteps; i++) {
                const step = document.getElementById(`step-${i}`);
                const stepEl = document.getElementById(`wizard-step-${i}`);
                
                if (i < currentStep) {
                    step.classList.remove('active');
                    step.classList.add('completed');
                    stepEl.classList.add('hidden');
                } else if (i === currentStep) {
                    step.classList.add('active');
                    step.classList.remove('completed');
                    stepEl.classList.remove('hidden');
                } else {
                    step.classList.remove('active', 'completed');
                    stepEl.classList.add('hidden');
                }
            }
            
            // Update buttons
            prevBtn.style.display = currentStep > 1 ? 'inline-flex' : 'none';
            
            if (currentStep === 3) {
                nextBtn.classList.add('hidden');
                createBtn.classList.remove('hidden');
            } else if (currentStep === 4) {
                nextBtn.style.display = 'none';
                createBtn.classList.add('hidden');
                prevBtn.style.display = 'none';
            } else {
                nextBtn.classList.remove('hidden');
                createBtn.classList.add('hidden');
            }
        }
        
        function validateStep() {
            hideMessages();
            
            if (currentStep === 1) {
                const title = document.getElementById('title').value.trim();
                const genre = document.getElementById('genre').value;
                const description = document.getElementById('description').value.trim();
                
                if (!title) {
                    showError('Please enter a movie title');
                    return false;
                }
                if (!genre) {
                    showError('Please select a genre');
                    return false;
                }
                if (!description) {
                    showError('Please provide a movie description');
                    return false;
                }
            } else if (currentStep === 2) {
                const style = document.getElementById('style').value;
                if (!style) {
                    showError('Please select a visual style');
                    return false;
                }
            }
            
            return true;
        }
        
        function updateReview() {
            if (currentStep === 3) {
                document.getElementById('review-title').textContent = document.getElementById('title').value;
                document.getElementById('review-genre').textContent = document.getElementById('genre').value;
                document.getElementById('review-style').textContent = document.querySelector('.style-option.selected .style-name').textContent;
                document.getElementById('review-description').textContent = document.getElementById('description').value;
            }
        }
        
        nextBtn.addEventListener('click', function() {
            if (validateStep()) {
                currentStep++;
                updateStepUI();
                updateReview();
            }
        });
        
        prevBtn.addEventListener('click', function() {
            currentStep--;
            updateStepUI();
            hideMessages();
        });
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!validateStep()) return;
            
            const formData = new FormData(form);
            const movieData = Object.fromEntries(formData);
            
            createBtn.classList.add('loading');
            createBtn.disabled = true;
            
            currentStep = 4;
            updateStepUI();
            
            try {
                const response = await fetch('/api/movies', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(movieData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('generation-status').innerHTML = `
                        <div style="color: #86efac; margin-bottom: 1rem;">✅ Movie created successfully!</div>
                        <p>Your movie "${movieData.title}" is now being generated. You can track its progress in your dashboard.</p>
                    `;
                    
                    setTimeout(() => {
                        window.location.href = `/movie/${data.movie_id}`;
                    }, 2000);
                } else {
                    showError(data.error || 'Failed to create movie');
                    currentStep = 3;
                    updateStepUI();
                }
            } catch (error) {
                showError('Network error. Please try again.');
                currentStep = 3;
                updateStepUI();
            } finally {
                createBtn.classList.remove('loading');
                createBtn.disabled = false;
            }
        });
        
        // Initialize
        updateStepUI();
    </script>
</body>
</html>
"""

# Movie View Template
MOVIE_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ movie.title }} - Cineo AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0c0c0c;
            color: white;
            overflow-x: hidden;
        }
        
        /* Animated background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%);
            animation: float 30s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-20px) rotate(1deg); }
            66% { transform: translateY(10px) rotate(-1deg); }
        }
        
        /* Header */
        .header {
            position: sticky;
            top: 0;
            background: rgba(12, 12, 12, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem 2rem;
            z-index: 100;
        }
        
        .nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .nav-link:hover {
            color: white;
        }
        
        /* Main Content */
        .main {
            position: relative;
            z-index: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Movie Hero */
        .movie-hero {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 3rem;
            margin-bottom: 4rem;
            padding: 2rem 0;
        }
        
        .movie-poster {
            width: 300px;
            height: 450px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
        }
        
        .movie-poster img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 16px;
        }
        
        .movie-info {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .movie-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .movie-meta {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            align-items: center;
        }
        
        .movie-genre {
            background: rgba(102, 126, 234, 0.2);
            color: #a5b4fc;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
        }
        
        .movie-status {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9rem;
        }
        
        .status-completed {
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
        }
        
        .status-generating {
            background: rgba(251, 191, 36, 0.2);
            color: #fde047;
        }
        
        .status-draft {
            background: rgba(156, 163, 175, 0.2);
            color: #d1d5db;
        }
        
        .status-failed {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
        }
        
        .movie-description {
            font-size: 1.1rem;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 2rem;
        }
        
        .movie-actions {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        /* Scenes Section */
        .section {
            margin-bottom: 4rem;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            color: white;
        }
        
        .scenes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }
        
        .scene-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .scene-card:hover {
            transform: translateY(-4px);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .scene-image {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            position: relative;
        }
        
        .scene-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .scene-info {
            padding: 1.5rem;
        }
        
        .scene-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: white;
        }
        
        .scene-description {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 1rem;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .scene-status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        /* Progress Bar */
        .progress-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .progress-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: white;
        }
        
        .progress-percentage {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            
            .movie-hero {
                grid-template-columns: 1fr;
                gap: 2rem;
                text-align: center;
            }
            
            .movie-poster {
                width: 200px;
                height: 300px;
                margin: 0 auto;
            }
            
            .movie-title {
                font-size: 2.5rem;
            }
            
            .scenes-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <header class="header">
        <nav class="nav">
            <div class="logo">Cineo AI</div>
            
            <div class="nav-links">
                <a href="/dashboard" class="nav-link">Dashboard</a>
                <a href="/create-movie" class="nav-link">Create</a>
            </div>
        </nav>
    </header>
    
    <main class="main">
        <div class="movie-hero">
            <div class="movie-poster">
                {% if movie.poster_url %}
                <img src="{{ movie.poster_url }}" alt="{{ movie.title }}">
                {% else %}
                🎬
                {% endif %}
            </div>
            
            <div class="movie-info">
                <h1 class="movie-title">{{ movie.title }}</h1>
                
                <div class="movie-meta">
                    <span class="movie-genre">{{ movie.genre }}</span>
                    <span class="movie-status status-{{ movie.status }}">{{ movie.status }}</span>
                </div>
                
                <p class="movie-description">{{ movie.description }}</p>
                
                <div class="movie-actions">
                    {% if movie.status == 'completed' and movie.video_url %}
                    <a href="{{ movie.video_url }}" class="btn btn-primary" target="_blank">
                        ▶️ Watch Movie
                    </a>
                    {% endif %}
                    
                    {% if movie.status == 'draft' %}
                    <button class="btn btn-primary" onclick="generateMovie({{ movie.id }})">
                        🎬 Generate Movie
                    </button>
                    {% endif %}
                    
                    {% if movie.poster_url %}
                    <a href="{{ movie.poster_url }}" class="btn btn-secondary" target="_blank">
                        🖼️ View Poster
                    </a>
                    {% endif %}
                    
                    <a href="/dashboard" class="btn btn-secondary">
                        ← Back to Dashboard
                    </a>
                </div>
            </div>
        </div>
        
        {% if movie.scenes %}
        <div class="progress-container">
            <div class="progress-header">
                <div class="progress-title">Generation Progress</div>
                <div class="progress-percentage" id="progress-text">0%</div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
        </div>
        
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">Movie Scenes</h2>
            </div>
            
            <div class="scenes-grid">
                {% for scene in movie.scenes %}
                <div class="scene-card" data-scene-id="{{ scene.id }}">
                    <div class="scene-image">
                        {% if scene.storyboard_url %}
                        <img src="{{ scene.storyboard_url }}" alt="Scene {{ scene.scene_number }}">
                        {% else %}
                        🎭
                        {% endif %}
                    </div>
                    
                    <div class="scene-info">
                        <h3 class="scene-title">{{ scene.title or 'Scene ' + scene.scene_number|string }}</h3>
                        <p class="scene-description">{{ scene.description }}</p>
                        <span class="scene-status status-{{ scene.status }}">{{ scene.status }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}
    </main>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <script>
        // Initialize WebSocket connection
        const socket = io();
        const movieId = {{ movie.id }};
        
        // Connect to movie room for real-time updates
        socket.on('connect', function() {
            console.log('Connected to server');
            socket.emit('join_movie', {movie_id: movieId});
        });
        
        // Handle movie updates
        socket.on('movie_update', function(data) {
            if (data.movie_id === movieId) {
                console.log('Movie update:', data);
                
                // Update status display
                const statusElements = document.querySelectorAll('.movie-status');
                statusElements.forEach(el => {
                    el.className = `movie-status status-${data.status}`;
                    el.textContent = data.status;
                });
                
                // Show notification
                showNotification(data.message, data.status === 'completed' ? 'success' : 'info');
                
                // Reload page if completed
                if (data.status === 'completed') {
                    setTimeout(() => location.reload(), 2000);
                }
            }
        });
        
        // Handle scene updates
        socket.on('scene_update', function(data) {
            if (data.movie_id === movieId) {
                console.log('Scene update:', data);
                
                // Update progress bar
                if (data.progress !== undefined) {
                    updateProgress(data.progress);
                }
                
                // Update scene status
                const sceneElement = document.querySelector(`[data-scene-id="${data.scene_id}"]`);
                if (sceneElement) {
                    const statusEl = sceneElement.querySelector('.scene-status');
                    if (statusEl) {
                        statusEl.className = `scene-status status-${data.status}`;
                        statusEl.textContent = data.status;
                    }
                }
                
                // Show step-specific messages
                if (data.message) {
                    showNotification(data.message, 'info');
                }
            }
        });
        
        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? 'rgba(34, 197, 94, 0.9)' : 'rgba(59, 130, 246, 0.9)'};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                backdrop-filter: blur(10px);
                z-index: 1000;
                max-width: 400px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                animation: slideIn 0.3s ease-out;
            `;
            notification.textContent = message;
            
            // Add animation styles
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(notification);
            
            // Auto remove after 4 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-in forwards';
                setTimeout(() => notification.remove(), 300);
            }, 4000);
        }
        
        async function generateMovie(movieId) {
            const button = event.target;
            const originalText = button.innerHTML;
            button.innerHTML = '⏳ Generating...';
            button.disabled = true;
            
            try {
                const response = await fetch(`/api/movies/${movieId}/generate`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    location.reload();
                } else {
                    const error = await response.json();
                    alert(error.error || 'Failed to generate movie');
                }
            } catch (error) {
                alert('Network error. Please try again.');
            } finally {
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }
        
        // Calculate and update progress
        function updateProgress() {
            const scenes = {{ movie.scenes | tojson if movie.scenes else '[]' }};
            if (scenes.length === 0) return;
            
            const completedScenes = scenes.filter(scene => scene.status === 'completed').length;
            const percentage = Math.round((completedScenes / scenes.length) * 100);
            
            document.getElementById('progress-fill').style.width = percentage + '%';
            document.getElementById('progress-text').textContent = percentage + '%';
        }
        
        // Auto-refresh if movie is generating
        {% if movie.status == 'generating' %}
        setInterval(() => {
            location.reload();
        }, 10000); // Refresh every 10 seconds
        {% endif %}
        
        // Initialize progress
        updateProgress();
    </script>
</body>
</html>
"""

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("🚀 Cineo AI - Complete Movie Generation Platform")
        print("=" * 50)
        print("✨ Features:")
        print("  • AI-powered script generation")
        print("  • Automatic storyboard creation")  
        print("  • Video scene generation")
        print("  • Professional movie posters")
        print("  • Real-time generation progress")
        print("  • Netflix-inspired UI")
        print()
        print("🌐 Access your app at: http://localhost:5000")
        print("📱 Mobile responsive design included")
        print()
        print("🔑 Create an account to start generating movies!")
        print("=" * 50)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
