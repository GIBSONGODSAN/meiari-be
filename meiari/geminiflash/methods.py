import hashlib
import random
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPTable

def generate_filename(base_name="generated_report"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.txt"

def encrypt_password(raw_password):
    salt = hashlib.sha256()
    salt.update(raw_password.encode('utf-8'))
    salt_bytes = salt.digest()

    hashed_password = hashlib.sha256()
    hashed_password.update(raw_password.encode('utf-8') + salt_bytes)
    hashed_password_bytes = hashed_password.digest()

    return hashed_password_bytes.hex()

def generate_otp():
    return random.randint(1000, 9999)

def meiariUser_encode_token(payload: dict):
    payload["exp"] = datetime.datetime.now(
        tz=datetime.timezone.utc
    ) + datetime.timedelta(days=7)
    token = jwt.encode(payload, "meiariUser_key", algorithm="HS256")
    return token

class EmailService:
    def send_otp_email(self, user):
        """Generate OTP, store it in the database, and send it via email."""
        otp = str(random.randint(1000, 9999))  # Generate a 4-digit OTP

        # Store OTP in OTPTable
        OTPTable.objects.create(user=user, otp=otp)

        # Email details
        subject = "Your OTP Code"
        message = f"Your OTP code is {otp}. Please use this to verify your account."

        # Send the OTP email
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

        print(f"✅ OTP {otp} sent to {user.email} and stored in OTPTable.")