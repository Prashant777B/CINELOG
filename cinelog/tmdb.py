from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
import requests
from datetime import datetime
from .models import Movie
from . import db

bp = Blueprint("tmdb", __name__)

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p"


def get_api_key():
    """Get TMDB API key from config"""
    key = current_app.config.get("TMDB_API_KEY")
    if not key:
        raise ValueError("TMDB_API_KEY not configured")
    return key


def tmdb_search(query, page=1):
    """Search for movies on TMDB"""
    try:
        key = get_api_key()
        response = requests.get(
            f"{TMDB_BASE}/search/movie",
            params={
                "api_key": key,
                "query": query,
                "include_adult": "false",
                "language": "en-US",
                "page": page
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"TMDB Search Error: {e}")
        return {"results": [], "total_pages": 0, "total_results": 0}


def tmdb_details(movie_id):
    """Get detailed movie information from TMDB"""
    try:
        key = get_api_key()
        response = requests.get(
            f"{TMDB_BASE}/movie/{movie_id}",
            params={
                "api_key": key,
                "language": "en-US"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"TMDB Details Error: {e}")
        return None


def tmdb_popular(page=1):
    """Get popular movies from TMDB"""
    try:
        key = get_api_key()
        response = requests.get(
            f"{TMDB_BASE}/movie/popular",
            params={
                "api_key": key,
                "language": "en-US",
                "page": page
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"TMDB Popular Error: {e}")
        return {"results": [], "total_pages": 0}


def tmdb_trending():
    """Get trending movies from TMDB"""
    try:
        key = get_api_key()
        response = requests.get(
            f"{TMDB_BASE}/trending/movie/week",
            params={
                "api_key": key,
                "language": "en-US"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"TMDB Trending Error: {e}")
        return {"results": []}


@bp.route("/search", methods=["GET"])
@login_required
def search():
    """Search movies using TMDB API"""
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    results = []
    total_pages = 0
    total_results = 0
    error = None

    if query:
        try:
            data = tmdb_search(query, page)
            results = data.get("results", [])
            total_pages = data.get("total_pages", 0)
            total_results = data.get("total_results", 0)
            
            if not results:
                flash(f"No results found for '{query}'", "info")
        except ValueError as e:
            error = str(e)
            flash("TMDB API key not configured. Please contact administrator.", "danger")
        except Exception as e:
            error = f"Search failed: {str(e)}"
            flash("Search failed. Please try again.", "danger")
    else:
        # Show popular movies if no query
        try:
            data = tmdb_popular(page)
            results = data.get("results", [])
            total_pages = data.get("total_pages", 0)
        except Exception:
            pass

    return render_template(
        "search.html",
        results=results,
        query=query,
        page=page,
        total_pages=min(total_pages, 500),  # TMDB limits to 500 pages
        total_results=total_results,
        tmdb_img_base=TMDB_IMG_BASE,
        error=error
    )


@bp.route("/movie/<int:tmdb_id>")
@login_required
def movie_details(tmdb_id):
    """Show detailed movie information"""
    details = tmdb_details(tmdb_id)
    
    if not details:
        flash("Could not fetch movie details.", "danger")
        return redirect(url_for("tmdb.search"))
    
    # Check if user already has this movie
    existing = Movie.query.filter_by(
        user_id=current_user.id,
        tmdb_id=tmdb_id
    ).first()
    
    return render_template(
        "movie_details.html",
        movie=details,
        existing=existing,
        tmdb_img_base=TMDB_IMG_BASE
    )


@bp.route("/import/<int:tmdb_id>", methods=["POST"])
@login_required
def import_tmdb(tmdb_id):
    """Import a movie from TMDB to user's library"""
    # Check if movie already exists for this user
    existing = Movie.query.filter_by(
        user_id=current_user.id,
        tmdb_id=tmdb_id
    ).first()
    
    if existing:
        flash(f"'{existing.title}' is already in your library.", "info")
        return redirect(url_for("routes.library"))
    
    # Fetch movie details from TMDB
    details = tmdb_details(tmdb_id)
    
    if not details:
        flash("Could not fetch movie details from TMDB.", "danger")
        return redirect(url_for("tmdb.search"))
    
    # Extract movie information
    title = details.get("title", "Untitled")
    release_date = details.get("release_date") or ""
    year = release_date[:4] if release_date else None
    poster_path = details.get("poster_path")
    backdrop_path = details.get("backdrop_path")
    overview = details.get("overview", "")
    runtime = details.get("runtime")
    vote_average = details.get("vote_average")
    
    # Get genres as comma-separated string
    genres = ", ".join([g["name"] for g in details.get("genres", [])])
    
    # Get status from form (default to watchlist)
    status = request.form.get("status", "watchlist")
    
    # Create movie entry
    movie = Movie(
        tmdb_id=tmdb_id,
        title=title,
        year=year,
        status=status,
        poster_path=poster_path,
        backdrop_path=backdrop_path,
        overview=overview,
        runtime=runtime,
        genres=genres,
        vote_average=vote_average,
        user_id=current_user.id
    )
    
    if status == "watched":
        movie.watched_at = datetime.utcnow()
    
    db.session.add(movie)
    db.session.commit()
    
    flash(f"✓ Added '{title}' to your library!", "success")
    return redirect(url_for("routes.library"))


@bp.route("/discover")
@login_required
def discover():
    """Discover trending and popular movies"""
    try:
        trending = tmdb_trending().get("results", [])[:10]
        popular = tmdb_popular().get("results", [])[:10]
    except Exception as e:
        flash("Could not load discover page.", "danger")
        trending = []
        popular = []
    
    return render_template(
        "discover.html",
        trending=trending,
        popular=popular,
        tmdb_img_base=TMDB_IMG_BASE
    )
