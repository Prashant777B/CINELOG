from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import requests
from .models import Movie
from . import db

bp = Blueprint("tmdb", __name__)

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"

def tmdb_search(query, key):
    print("TMDB Search Query:", query)
    r = requests.get(
        f"{TMDB_BASE}/search/movie",
        params={
            "api_key": key,
            "query": query,
            "include_adult": "false"
        }
    )
    print("TMDB Response:", r.status_code)
    r.raise_for_status()
    return r.json().get("results", [])

def tmdb_details(movie_id, key):
    r = requests.get(f"{TMDB_BASE}/movie/{movie_id}", params={"api_key": key})
    r.raise_for_status()
    return r.json()

@bp.route("/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("q", "").strip()
    results = []
    error = None

    api_key = current_app.config.get("TMDB_API_KEY")

    print("TMDB Search Query:", query)

    if query:
        try:
            response = requests.get(
                f"{TMDB_BASE}/search/movie",
                params={
                    "api_key": api_key,
                    "query": query,
                    "include_adult": "false",
                    "language": "en-US",
                }
            )
            print("TMDB Response Code:", response.status_code)
            data = response.json()
            print("TMDB Response JSON:", data)  # <-- Debug

            results = data.get("results", [])

        except Exception as e:
            error = f"Search failed: {str(e)}"

    return render_template(
        "search.html",
        results=results,
        query=query,
        tmdb_img_base=TMDB_IMG,
        error=error
    )

@bp.route("/import/<int:movie_id>", methods=["POST"])
@login_required
def import_tmdb(movie_id):
    api_key = current_app.config.get("TMDB_API_KEY")
    if not api_key:
        flash("TMDB API key missing.", "danger")
        return redirect(url_for("tmdb.search"))

    details = tmdb_details(movie_id, api_key)
    title = details.get("title", "Untitled")
    release_date = details.get("release_date") or ""
    year = release_date[:4] if release_date else None

    movie = Movie(
        title=title,
        year=year,
        status="watchlist",
        user_id=current_user.id
    )
    db.session.add(movie)
    db.session.commit()

    flash(f"Imported “{title}” from TMDB.", "success")
    return redirect(url_for("routes.library"))
