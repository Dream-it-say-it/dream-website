from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.message import EmailMessage

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

    conn.commit()
    conn.close()

init_db()

# ---------------- AI MATCH ----------------
def find_similar(dream, all_dreams):
    matches = []
    words = set(dream.lower().split())

    for d in all_dreams:
        common = words.intersection(set(d[1].lower().split()))
        if len(common) > 2:
            matches.append(d)

    return matches

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html', dreams=[])

# ---------------- SUBMIT ----------------
@app.route('/submit', methods=['POST'])
def submit():
    try:
        username = request.form.get('username', 'Anonymous')
        dream = request.form.get('dream')

        # prevent crash if empty
        if not dream or dream.strip() == "":
            return "Please enter a dream."

        conn = sqlite3.connect('dreams.db')
        c = conn.cursor()

        # get old dreams
        c.execute("SELECT username, dream FROM dreams")
        all_dreams = c.fetchall()

        # find similar
        similar = find_similar(dream, all_dreams)

        # save dream
        c.execute("INSERT INTO dreams (username, dream) VALUES (?, ?)", (username, dream))

        # update streak
        if username != "Anonymous":
            c.execute("UPDATE users SET streak = streak + 1 WHERE username = ?", (username,))

        conn.commit()
        conn.close()

        # ---------------- EMAIL ----------------
        try:
            msg = EmailMessage()
            msg.set_content(f"User: {username}\n\nDream:\n{dream}\n\nSimilar: {len(similar)}")
            msg['Subject'] = "⚠️ New Dream Submission"
            msg['From'] = "your_email@gmail.com"
            msg['To'] = "your_email@gmail.com"

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("ajiboyecomfort971@gmail.com", "fwtiozcenbzofirc")
                smtp.send_message(msg)

        except Exception as e:
            # email fails but app still works
            print("Email failed:", e)

        return "Your dream has been recorded."

    except Exception as e:
        return f"Error: {str(e)}"

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
            return redirect('/')
        else:
            return "Invalid login"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
