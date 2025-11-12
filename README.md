# CineLog (Modular Flask App)

A clean, modular Flask app with SQLite, Bootstrap templates, and TMDB-powered search.

## Setup

```bash
python -m venv env
# Windows
env\Scripts\activate
# Install deps
pip install -r requirements.txt
# Set your TMDB API key (get it from themoviedb.org)
set TMDB_API_KEY=YOUR_TMDB_KEY
# Initialize DB
flask --app app init-db
# Run
flask --app app run
```

## Notes
- TMDB API key is read from the `TMDB_API_KEY` environment variable.
- Database is SQLite (`cinelog.db`) for easy marking/testing.
- Templates use Bootstrap 5.
