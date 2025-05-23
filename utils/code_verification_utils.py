from datetime import datetime, timedelta, timezone
import random


def generate_verification_code():
    return random.randint(100000, 999999)

def is_code_valid(user, code, expiry_minutes=10):
    if not user.verification_code or user.verification_code != int(code):
        return False

    if not user.code_sent_at:
        return False

    now_utc = datetime.now(timezone.utc)

    # Ensure user.code_sent_at is also timezone-aware
    sent_at_utc = user.code_sent_at
    if sent_at_utc.tzinfo is None:
        sent_at_utc = sent_at_utc.replace(tzinfo=timezone.utc)

    return now_utc - sent_at_utc < timedelta(minutes=expiry_minutes)


def is_email_code_valid(user, code, expiry_minutes=10):
    if not user.email_verification_code or user.email_verification_code != int(code):
        return False
    return datetime.now(timezone.utc) - user.email_code_sent_at < timedelta(minutes=expiry_minutes)