from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streammax.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-streammax-key-2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads/videos'
app.config['POSTER_FOLDER'] = 'static/uploads/posters'
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024 # 2GB limit

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    poster_url = db.Column(db.String(255), nullable=True)
    qualities = db.Column(db.String(255), nullable=True) # JSON string of selected qualities
    video_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_qualities_list(self):
        try:
            return json.loads(self.qualities)
        except:
            return []

with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['POSTER_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template('index.html', movies=movies)

@app.route('/movie/<int:id>')
def movie_detail(id):
    movie = Movie.query.get_or_404(id)
    return render_template('movie.html', movie=movie)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    movies_count = Movie.query.count()
    return render_template('admin.html', movies_count=movies_count)

@app.route('/admin/add-movie', methods=['POST'])
def add_movie():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    release_year = request.form.get('year')
    genre = request.form.get('genre')
    description = request.form.get('description')
    
    # Handle poster file upload
    poster_url = request.form.get('poster_url') # Default to URL if provided
    if 'poster' in request.files:
        file = request.files['poster']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            save_path = os.path.join(app.config['POSTER_FOLDER'], unique_filename)
            file.save(save_path)
            poster_url = f"uploads/posters/{unique_filename}"
    
    # Handle video file upload
    video_path = None
    if 'video' in request.files:
        file = request.files['video']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)
            video_path = f"uploads/videos/{unique_filename}"
    
    # Extract selected qualities
    qualities = request.form.getlist('qualities')
    
    new_movie = Movie(
        title=title,
        release_year=int(release_year) if release_year else 0,
        genre=genre,
        description=description,
        poster_url=poster_url,
        qualities=json.dumps(qualities),
        video_path=video_path
    )
    db.session.add(new_movie)
    db.session.commit()
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
