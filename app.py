import smtplib
from email.message import EmailMessage

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username', 'Anonymous')
    dream = request.form['dream']

    msg = EmailMessage()
    msg.set_content(f"User: {username}\n\nDream:\n{dream}")
    msg['Subject'] = "New Dream Submission"
    msg['From'] = "your_email@gmail.com"
    msg['To'] = "your_email@gmail.com"

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login("your_email@gmail.com", "your_app_password")
        smtp.send_message(msg)

    return "Recorded."
