import smtplib
from email.mime.text import MIMEText

def send_email_alert(signal, confidence, recipient):
    sender_email = "your_email@example.com"
    app_password = "your_app_password"  # Consider storing in secrets manager

    subject = f"📢 Trade Signal: {signal}"
    body = f"New trade signal generated.\n\nSignal: {signal}\nConfidence: {confidence:.2f}%"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
            print("✅ Email alert sent.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")