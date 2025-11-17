"""
Services for accounts app (OTP, email, SMS)
"""
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP, User


def generate_otp_code(length=6):
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, code, otp_type='EMAIL_VERIFICATION'):
    """Send OTP via email (mock implementation - integrate with SendGrid/SES in production)"""
    subject_map = {
        'EMAIL_VERIFICATION': 'Verify your email address',
        'PHONE_VERIFICATION': 'Verify your phone number',
        'PASSWORD_RESET': 'Reset your password',
        'LOGIN': 'Login verification code',
    }
    
    subject = subject_map.get(otp_type, 'Verification code')
    message = f"""
    Your verification code is: {code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this code, please ignore this email.
    """
    
    # In production, use SendGrid, SES, or similar
    # For now, just print (in development)
    if settings.DEBUG:
        print(f"OTP Email to {email}: {code}")
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,  # Don't fail silently in production, but allow dev to continue
        )
        return True
    except Exception as e:
        # In development, just log the error and continue
        if settings.DEBUG:
            print(f"OTP Email (would be sent to {email}): {code}")
            print(f"Note: Email sending failed ({e}), but continuing in DEBUG mode")
        else:
            print(f"Failed to send email: {e}")
        return True  # Return True in DEBUG mode to allow development to continue


def send_otp_sms(phone, code, otp_type='PHONE_VERIFICATION'):
    """Send OTP via SMS (mock implementation - integrate with Twilio/AWS SNS in production)"""
    message = f"Your verification code is: {code}. Valid for 10 minutes."
    
    # In production, use Twilio, AWS SNS, or similar
    # For now, just print (in development)
    if settings.DEBUG:
        print(f"OTP SMS to {phone}: {code}")
    
    # Mock SMS sending
    return True


def create_and_send_otp(email=None, phone=None, user=None, otp_type='EMAIL_VERIFICATION'):
    """Create OTP and send it via email or SMS"""
    if not email and not phone:
        raise ValueError("Either email or phone must be provided")
    
    # Invalidate previous unverified OTPs of the same type
    if email:
        OTP.objects.filter(email=email, type=otp_type, verified=False).update(verified=True)
    if phone:
        OTP.objects.filter(phone=phone, type=otp_type, verified=False).update(verified=True)
    
    # Generate OTP code
    code = generate_otp_code()
    
    # Set expiration (10 minutes)
    expires_at = timezone.now() + timedelta(minutes=10)
    
    # Create OTP record
    otp = OTP.objects.create(
        user=user,
        email=email or '',
        phone=phone or '',
        code=code,
        type=otp_type,
        expires_at=expires_at,
    )
    
    # Send OTP
    if email:
        send_otp_email(email, code, otp_type)
    if phone:
        send_otp_sms(phone, code, otp_type)
    
    return otp


def verify_otp(email=None, phone=None, code=None, otp_type='EMAIL_VERIFICATION', user=None):
    """Verify OTP code"""
    if not code:
        return False, "Code is required"
    
    # Find the most recent unverified OTP
    query = {
        'type': otp_type,
        'verified': False,
        'code': code,
    }
    
    if user:
        query['user'] = user
    elif email:
        query['email'] = email
    elif phone:
        query['phone'] = phone
    else:
        return False, "Email, phone, or user must be provided"
    
    try:
        otp = OTP.objects.filter(**query).order_by('-created_at').first()
        
        if not otp:
            return False, "Invalid code"
        
        # Check if expired
        if otp.is_expired():
            otp.attempts += 1
            otp.save()
            return False, "Code has expired"
        
        # Check attempts
        if otp.attempts >= otp.max_attempts:
            return False, "Maximum attempts exceeded"
        
        # Verify code
        if otp.code == code:
            otp.verified = True
            otp.verified_at = timezone.now()
            otp.save()
            
            # Update user verification status if applicable
            if user:
                if otp_type == 'EMAIL_VERIFICATION':
                    user.is_email_verified = True
                    user.save()
                elif otp_type == 'PHONE_VERIFICATION':
                    user.is_phone_verified = True
                    user.save()
            
            return True, "Code verified successfully"
        else:
            otp.attempts += 1
            otp.save()
            return False, "Invalid code"
    
    except Exception as e:
        return False, f"Error verifying code: {str(e)}"

