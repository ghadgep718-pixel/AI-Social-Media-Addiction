# Addict-Analyzer (professional front-end polish)

Quick local setup to run the Flask demo app that analyzes basic social media usage.

Prerequisites
- Python 3.8+

Install and run

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/ in your browser. Pages available:
- `/` — Home analyzer (`templates/index.html`)
- `/result` — Analysis result (`templates/result.html`)
- `/about` — About page (`templates/about.html`)
- `/signin` — Sign in page (`templates/signin.html`)
- `/signup` — Sign up page (`templates/signup.html`)

Notes
- Static CSS is at `static/styles.css` and templates are in `templates/`.
- This is a demo; submission handlers for sign-in/sign-up are placeholders and do not create users.
# Social Media Addiction Analyzer (Simple)

Beginner-friendly Flask app that saves daily social media usage to an SQLite database and shows a simple addiction analysis.

Files created:
- `app.py` - main Flask app (single file)
- `templates/index.html` - form to submit daily usage
- `templates/result.html` - shows analysis and warnings
- `addiction.db` - created automatically when running the app
- `requirements.txt` - lists Flask

Run locally:

```powershell
pip install -r requirements.txt
python app.py
# then open http://127.0.0.1:5000/ in your browser
```

The app uses only Flask and sqlite3 and is meant for learning and demonstration.
