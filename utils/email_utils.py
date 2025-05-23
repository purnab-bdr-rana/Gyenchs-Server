import smtplib
from email.message import EmailMessage
import os
import threading

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email_verification(to_email, subject, html_body, plain_body=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(plain_body or "Please use an HTML-compatible email viewer.")
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_verification_email(email, subject, code):
    html_body = f"""
    <div style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
      <div style="max-width: 500px; margin: auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #534ca0; text-align: center;">Your Verification Code</h2>
        <p style="font-size: 16px; color: #333; text-align: center;">
          Use the verification code below to confirm your identity.
        </p>
        <div style="text-align: center; margin: 30px 0;">
          <span style="font-size: 28px; font-weight: bold; color: #6b52a2; background: #eee; padding: 12px 24px; border-radius: 8px;">{code}</span>
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
          This code will expire in <strong>10 minutes</strong> for security reasons.
        </p>
        <p style="font-size: 13px; color: #999; text-align: center; margin-top: 30px;">
          If you did not request this, please ignore this email.
        </p>
      </div>
    </div>
    """

    plain_body = f"Your verification code is: {code}. It will expire in 10 minutes."

    return send_email_verification(email, subject, html_body, plain_body)



def send_login_alert_email_async(user_email, now, device, location):
    def task():
        html_body = f"""
        <div style='font-family: Arial; background-color: #f9f9f9; padding: 20px;'>
          <div style='max-width: 500px; margin: auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
            <h2 style='color: #534ca0; text-align: center;'>Login Notification</h2>
            <p style='font-size: 16px; color: #333; text-align: center;'>
              A login to your account was made:
            </p>
            <ul style='font-size: 14px; color: #555;'>
              <li><strong>Time:</strong> {now}</li>
              <li><strong>Device:</strong> {device}</li>
              <li><strong>Location:</strong> {location}</li>
            </ul>
            <p style='font-size: 13px; color: #999; text-align: center; margin-top: 20px;'>
              If this wasn't you, please reset your password immediately.
            </p>
          </div>
        </div>
        """

        plain_body = (f"Login detected:\n"
                      f"- Time: {now}\n"
                      f"- Device: {device}\n"
                      f"- Location: {location}\n\n"
                      f"If this wasn't you, please change your password.")

        send_email_verification(user_email, "Login Alert", html_body, plain_body)

    # Start thread
    threading.Thread(target=task).start()