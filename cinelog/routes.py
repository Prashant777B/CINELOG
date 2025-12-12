from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime
from .models import User, Movie, Review
from . import db

bp = Blueprint("routes", __name__)


@bp.route("/")
def home():
    """Home page - redirect to dashboard if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    return render_template("home.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("routes.register"))
        
        if len(username) < 3:
            flash("Username must be at least 3 characters.", "warning")
            return redirect(url_for("routes.register"))
        
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for("routes.register"))
        
        # Check if user exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("routes.register"))
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash("✓ Registration successful! Please log in.", "success")
        return redirect(url_for("routes.login"))
    
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        remember = request.form.get("remember", False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 🎬", "success")
            return redirect(next_page if next_page else url_for("routes.dashboard"))
        
        flash("Invalid username or password.", "danger")
    
    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    """User logout"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("routes.home"))


@bp.route("/dashboard")
@login_required
def dashboard():
    """User dashboard with statistics"""
    movies = Movie.query.filter_by(user_id=current_user.id).all()
    
    total_count = len(movies)
    watched_count = sum(1 for m in movies if m.status == "watched")
    watchlist_count = sum(1 for m in movies if m.status == "watchlist")
    watching_count = sum(1 for m in movies if m.status == "watching")
    
    # Calculate total runtime for watched movies
    total_runtime = sum(m.runtime or 0 for m in movies if m.status == "watched")
    hours = total_runtime // 60
    minutes = total_runtime % 60
    
    # Get recently added movies
    recent_movies = Movie.query.filter_by(user_id=current_user.id)\
        .order_by(Movie.added_at.desc())\
        .limit(6)\
        .all()
    
    # Get recent reviews
    recent_reviews = Review.query.filter_by(user_id=current_user.id)\
        .order_by(Review.created_at.desc())\
        .limit(5)\
        .all()
    
    return render_template(
        "dashboard.html",
        movie_count=total_count,
        watched=watched_count,
        watchlist=watchlist_count,
        watching=watching_count,
        total_hours=hours,
        total_minutes=minutes,
        recent_movies=recent_movies,
        recent_reviews=recent_reviews
    )


@bp.route("/library")
@login_required
def library():
    """User's movie library with filtering and sorting"""
    # Get filter and sort parameters
    status_filter = request.args.get("filter", "all")
    sort_by = request.args.get("sort", "added")
    
    # Base query
    query = Movie.query.filter_by(user_id=current_user.id)
    
    # Apply status filter
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    
    # Apply sorting
    if sort_by == "title":
        query = query.order_by(Movie.title)
    elif sort_by == "year":
        query = query.order_by(Movie.year.desc())
    elif sort_by == "rating":
        query = query.order_by(Movie.user_rating.desc().nullslast())
    else:  # default: added
        query = query.order_by(Movie.added_at.desc())
    
    movies = query.all()
    
    return render_template(
        "library.html",
        movies=movies,
        current_filter=status_filter,
        current_sort=sort_by
    )


@bp.route("/movie/<int:movie_id>")
@login_required
def movie_detail(movie_id):
    """View movie details"""
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("routes.library"))
    
    reviews = Review.query.filter_by(movie_id=movie.id, user_id=current_user.id)\
        .order_by(Review.created_at.desc())\
        .all()
    
    return render_template("movie_detail.html", movie=movie, reviews=reviews)


@bp.route("/update_status/<int:movie_id>", methods=["POST"])
@login_required
def update_status(movie_id):
    """Update movie watch status"""
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("routes.library"))
    
    new_status = request.form.get("status")
    
    # Validate status
    if new_status not in ["watchlist", "watching", "watched"]:
        flash("Invalid status.", "danger")
        return redirect(url_for("routes.library"))
    
    movie.status = new_status
    
    # Set watched_at timestamp if marking as watched
    if new_status == "watched" and not movie.watched_at:
        movie.watched_at = datetime.utcnow()
    
    db.session.commit()
    flash(f"✓ Updated '{movie.title}' status to {new_status}.", "success")
    
    return redirect(request.referrer or url_for("routes.library"))


@bp.route("/rate/<int:movie_id>", methods=["POST"])
@login_required
def rate_movie(movie_id):
    """Rate a movie"""
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("routes.library"))
    
    rating = request.form.get("rating", type=int)
    
    if rating and 1 <= rating <= 10:
        movie.user_rating = rating
        db.session.commit()
        flash(f"✓ Rated '{movie.title}' {rating}/10", "success")
    else:
        flash("Invalid rating. Please rate between 1-10.", "warning")
    
    return redirect(request.referrer or url_for("routes.library"))


@bp.route("/review/<int:movie_id>", methods=["GET", "POST"])
@login_required
def review(movie_id):
    """Add or view reviews for a movie"""
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("routes.library"))
    
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        rating = request.form.get("rating", type=int)
        
        if not content:
            flash("Review cannot be empty.", "warning")
        else:
            review = Review(
                content=content,
                rating=rating if rating and 1 <= rating <= 10 else None,
                movie_id=movie.id,
                user_id=current_user.id
            )
            db.session.add(review)
            
            # Update movie rating if provided
            if rating and 1 <= rating <= 10:
                movie.user_rating = rating
            
            db.session.commit()
            flash("✓ Review added successfully!", "success")
            return redirect(url_for("routes.review", movie_id=movie.id))
    
    reviews = Review.query.filter_by(movie_id=movie.id, user_id=current_user.id)\
        .order_by(Review.created_at.desc())\
        .all()
    
    return render_template("review.html", movie=movie, reviews=reviews)


@bp.route("/delete_movie/<int:movie_id>", methods=["POST"])
@login_required
def delete_movie(movie_id):
    """Delete a movie from library"""
    movie = Movie.query.filter_by(id=movie_id, user_id=current_user.id).first()
    
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("routes.library"))
    
    title = movie.title
    db.session.delete(movie)
    db.session.commit()
    
    flash(f"✓ Removed '{title}' from your library.", "success")
    return redirect(url_for("routes.library"))


@bp.route("/delete_review/<int:review_id>", methods=["POST"])
@login_required
def delete_review(review_id):
    """Delete a review"""
    review = Review.query.filter_by(id=review_id, user_id=current_user.id).first()
    
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("routes.library"))
    
    movie_id = review.movie_id
    db.session.delete(review)
    db.session.commit()
    
    flash("✓ Review deleted.", "success")
    return redirect(url_for("routes.review", movie_id=movie_id))
