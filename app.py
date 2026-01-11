from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Database filename and connection timeout (seconds)
DB_NAME = 'addiction.db'
DB_TIMEOUT = 30


def get_db_connection():
    """Return a new sqlite3 connection configured to reduce locking.

    - Uses a longer timeout so short locks don't fail immediately.
    - `check_same_thread=False` allows the connection to be used safely
      across threads if the app server is threaded (we create per-call
      connections, so this is safe).
    """
    conn = sqlite3.connect(DB_NAME, timeout=DB_TIMEOUT, check_same_thread=False)
    return conn


def init_db():
    """Create required SQLite tables if they don't exist and enable WAL."""
    conn = get_db_connection()
    c = conn.cursor()
    # Enable WAL journal mode to reduce write-lock contention
    try:
        c.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        # pragma may fail on very old SQLite builds; ignore in that case
        pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            instagram REAL,
            youtube REAL,
            whatsapp REAL,
            screen_time REAL,
            sleep_hours REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Create the Flask app
app = Flask(__name__)
# Development secret key (replace in production)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-key')

# Ensure the database is ready when the app starts
init_db()


@app.route('/')
def index():
    """Home page with the daily usage form."""
    return render_template('index.html', user_name=session.get('user_name'))


@app.route('/add', methods=['POST'])
def add():
    """Receive form data, save to the SQLite DB, then redirect to result."""
    # Require authenticated user
    if not session.get('user_id'):
        return redirect(url_for('signin'))

    try:
        # Read form values and convert to floats
        name = request.form.get('name', '').strip()
        instagram = float(request.form.get('instagram', 0) or 0)
        youtube = float(request.form.get('youtube', 0) or 0)
        whatsapp = float(request.form.get('whatsapp', 0) or 0)
        screen_time = float(request.form.get('screen_time', 0) or 0)
        sleep_hours = float(request.form.get('sleep_hours', 0) or 0)

        # Insert into database using a context manager so connections close on error
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO usage (name, instagram, youtube, whatsapp, screen_time, sleep_hours) VALUES (?,?,?,?,?,?)',
                (name, instagram, youtube, whatsapp, screen_time, sleep_hours)
            )
            last_id = c.lastrowid

        # Redirect to result page for the saved record
        return redirect(url_for('result', record_id=last_id))
    except Exception as e:
        # Simple error handling for beginners
        return f"Error saving data: {e}", 500


@app.route('/result')
def result():
    """Show analysis for a saved record identified by `record_id` query param."""
    record_id = request.args.get('record_id')
    if not record_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    try:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM usage WHERE id = ?', (record_id,))
        row = c.fetchone()
    finally:
        conn.close()

    if not row:
        return 'Record not found', 404

    # Calculate total social media usage (instagram + youtube + whatsapp)
    total_social = row['instagram'] + row['youtube'] + row['whatsapp']

    # Determine addiction level based on screen_time (hours)
    st = row['screen_time']
    if st > 6:
        level = 'High Addiction'
        warning = 'High risk: consider limiting screen time, taking regular breaks, and seeking support if needed.'
    elif 3 <= st <= 6:
        level = 'Moderate Addiction'
        warning = 'Moderate risk: try scheduling screen-free periods and reduce night-time usage.'
    else:
        level = 'Low Addiction'
        warning = 'Low risk: maintain these healthy habits and good sleep.'

    # Render the result template
    return render_template(
        'result.html',
        name=row['name'],
        instagram=row['instagram'],
        youtube=row['youtube'],
        whatsapp=row['whatsapp'],
        total_social=total_social,
        screen_time=st,
        sleep_hours=row['sleep_hours'],
        level=level,
        warning=warning
    )


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Simple sign-in page. POST will redirect to home for now."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not email or not password:
            return render_template('signin.html', error='Missing email or password')

        conn = get_db_connection()
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = c.fetchone()
        finally:
            conn.close()

        if not user:
            return render_template('signin.html', error='No account for that email')

        if not check_password_hash(user['password_hash'], password):
            return render_template('signin.html', error='Invalid credentials')

        # Successful sign-in: set session and redirect to personalized home
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        flash('Successfully signed in', 'success')
        return redirect(url_for('index'))

    return render_template('signin.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Simple sign-up page. POST will redirect to home for now."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            return render_template('signup.html', error='All fields required')

        password_hash = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (name, email, password_hash) VALUES (?,?,?)',
                          (name, email, password_hash))
                last_id = c.lastrowid
        except sqlite3.IntegrityError:
            # Email already exists
            return render_template('signup.html', error='Email already registered')

        except Exception as e:
            # Log unexpected exceptions to console for debugging
            import traceback
            traceback.print_exc()
            return render_template('signup.html', error=f'Unexpected error: {e}')

        # Auto sign-in new user
        session['user_id'] = last_id
        session['user_name'] = name
        flash('Successfully signed up', 'success')
        return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/signout')
def signout():
    """Sign the user out by clearing the session."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/analyze')
def analyze():
    """Render the analyzer form for signed-in users."""
    if not session.get('user_id'):
        return redirect(url_for('signin'))
    return render_template('analyze.html', user_name=session.get('user_name'))


if __name__ == '__main__':
    # Run the app without the auto-reloader so it stays stable during local testing.
    # Bind to 0.0.0.0 so other tools on this machine can reach it; keep debug off.
    # Enable debug=True temporarily to surface exceptions during local testing.
    app.run(host='0.0.0.0', port=5000, debug=True)
