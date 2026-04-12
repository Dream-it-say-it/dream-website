from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def init_db():
    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
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

@app.route('/')
def home():
    try:
        conn = sqlite3.connect('dreams.db')
        c = conn.cursor()
        c.execute("SELECT username, dream FROM dreams ORDER BY id DESC")
        dreams = c.fetchall()
        conn.close()
        return render_template('index.html', dreams=dreams)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit():
    if 'user' in session:
        username = session['user']
    else:
        username = "Anonymous"

    dream = request.form['dream']

    conn = sqlite3.connect('dreams.db')
    c = conn.cursor()
    c.execute("INSERT INTO dreams (username, dream) VALUES (?, ?)", (username, dream))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

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
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('dreams.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
