from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    reviews = db.relationship("Review", backref="user", lazy=True, cascade="all, delete-orphan")
    movies = db.relationship("Movie", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer)  # Store TMDB ID for reference
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(10))
    status = db.Column(db.String(50), default="watchlist")  # watchlist, watched, watching
    poster_path = db.Column(db.String(300))
    backdrop_path = db.Column(db.String(300))
    overview = db.Column(db.Text)
    runtime = db.Column(db.Integer)  # in minutes
    genres = db.Column(db.String(200))  # comma-separated genre names
    vote_average = db.Column(db.Float)
    user_rating = db.Column(db.Integer)  # personal rating 1-10
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    watched_at = db.Column(db.DateTime)
    
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # relationships
    reviews = db.relationship("Review", backref="movie", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Movie {self.title}>"


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-10 rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movie.id"), nullable=False)

    def __repr__(self):
        return f"<Review {self.id} for Movie {self.movie_id}>"
