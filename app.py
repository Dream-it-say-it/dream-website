from flask import Flask, render_template, request, redirect
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
        if not d[1]:
            continue
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

    # AI check
    c.execute("SELECT username, dream FROM dreams")
    all_dreams = c.fetchall()
    similar = find_similar(dream, all_dreams)

    # save dream
    c.execute(
        "INSERT INTO dreams (username, dream) VALUES (?, ?)",
        (username, dream)
    )

    conn.commit()
    conn.close()

    # ---------------- EMAIL NOTIFICATION ----------------
    try:
        msg = EmailMessage()
        msg.set_content(f"User: {username}\n\nDream:\n{dream}")
        msg['Subject'] = "⚠️ New Dream Submitted"
        msg['From'] = "your_email@gmail.com"
        msg['To'] = "your_email@gmail.com"

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("your_email@gmail.com", "your_app_password")
            smtp.send_message(msg)

    except Exception as e:
        print("Email failed:", e)  # doesn't crash app

    # ---------------- RESPONSE ----------------
    if len(similar) > 0:
        return "⚠️ Someone else has reported a similar dream..."

    return "Your dream has been recorded."

# ---------------- REPLY SYSTEM ----------------
@app.route('/reply', methods=['POST'])
def reply():
    dream_id = request.form.get('dream_id')
    reply_text = request.form.get('reply')

    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO replies (dream_id, reply) VALUES (?, ?)",
        (dream_id, reply_text)
    )

    conn.commit()
    conn.close()

    return redirect('/admin?key=secret123')

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if request.args.get("key") != "secret123":
        return "Access denied"

    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute("SELECT id, username, dream FROM dreams ORDER BY id DESC")
    dreams = c.fetchall()

    conn.close()

    return render_template('admin.html', dreams=dreams)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
