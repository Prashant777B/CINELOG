from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Movie
from . import db

bp = Blueprint("routes", __name__)

@bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    return render_template("home.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("routes.register"))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("routes.register"))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("routes.login"))
    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("routes.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.home"))

@bp.route("/dashboard")
@login_required
def dashboard():
    count = Movie.query.filter_by(user_id=current_user.id).count()
    watched = Movie.query.filter_by(user_id=current_user.id, status="watched").count()
    watchlist = Movie.query.filter_by(user_id=current_user.id, status="watchlist").count()
    return render_template("dashboard.html", movie_count=count, watched=watched, watchlist=watchlist)

@bp.route("/library")
@login_required
def library():
    movies = Movie.query.filter_by(user_id=current_user.id).all()
    return render_template("library.html", movies=movies)

@bp.route("/add_movie", methods=["GET", "POST"])
@login_required
def add_movie():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year = request.form.get("year", "").strip() or None
        status = request.form.get("status", "watchlist")
        if not title:
            flash("Title is required.", "warning")
            return redirect(url_for("routes.add_movie"))
        m = Movie(title=title, year=year, status=status, user_id=current_user.id)
        db.session.add(m)
        db.session.commit()
        flash("Movie added.", "success")
        return redirect(url_for("routes.library"))
    return render_template("add_movie.html")
