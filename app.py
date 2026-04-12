from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        streak INTEGER DEFAULT 0
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS dreams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        dream TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dream_id INTEGER,
        reply TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- SIMPLE AI MATCH ----------------
def find_similar(dream, all_dreams):
    words = set(dream.lower().split())
    matches = []

    for d in all_dreams:
        common = words.intersection(set(d[1].lower().split()))
        if len(common) >= 3:
            matches.append(d)

    return matches

# ---------------- HOME ----------------
@app.route('/')
def home():
    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute("""
    SELECT dreams.id, dreams.username, dreams.dream, replies.reply
    FROM dreams
    LEFT JOIN replies ON dreams.id = replies.dream_id
    ORDER BY dreams.id DESC
    """)

    dreams = c.fetchall()
    conn.close()

    return render_template('index.html', dreams=dreams)

# ---------------- SUBMIT ----------------
@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username', 'Anonymous')
    dream = request.form.get('dream')

    if not dream or dream.strip() == "":
        return "Please enter a dream."

    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    # get old dreams for AI check
    c.execute("SELECT username, dream FROM dreams")
    all_dreams = c.fetchall()

    similar = find_similar(dream, all_dreams)

    # save dream
    c.execute("INSERT INTO dreams (username, dream) VALUES (?, ?)", (username, dream))

    # streak system
    if username != "Anonymous":
        c.execute("UPDATE users SET streak = streak + 1 WHERE username = ?", (username,))

    conn.commit()
    conn.close()

    # response message
    if len(similar) > 0:
        return "⚠️ Someone else has reported a similar dream..."
    return "Your dream has been recorded."

# ---------------- REPLY SYSTEM ----------------
@app.route('/reply', methods=['POST'])
def reply():
    if 'user' not in session:
        return redirect('/login')

    dream_id = request.form.get('dream_id')
    reply_text = request.form.get('reply')

    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute("INSERT INTO replies (dream_id, reply) VALUES (?, ?)", (dream_id, reply_text))

    conn.commit()
    conn.close()

    return redirect('/admin')

# ---------------- ADMIN (LOGIN PROTECTED) ----------------
@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute("SELECT id, username, dream FROM dreams ORDER BY id DESC")
    dreams = c.fetchall()

    conn.close()

    return render_template('admin.html', dreams=dreams)

# ---------------- AUTH ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Fill all fields."

        conn = sqlite3.connect('dreams.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('dreams.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/admin')
        else:
            return "Invalid login"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
