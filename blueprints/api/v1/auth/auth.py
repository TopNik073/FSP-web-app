import logging
from datetime import datetime

from flask import Blueprint, request
from werkzeug.security import check_password_hash, generate_password_hash

from DB.user import User
from DB.token import Token
from DB.models.enums.token_types import TokenTypes
from blueprints.api.v1.responses import get_200, get_400, get_500, get_404
from emailer.EmailService import EmailService

auth = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth.post("/login")
def login():
    try:
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return get_400("Email and password are required")
        
        user: User = User(email=email, auto_add=False)
        if user.get() is None:
            return get_404("User not found")
        
        if not check_password_hash(user.password, password):
            return get_400("Invalid password")
        
        if not user.is_verified:
            return get_400("User is not verified")
        
        return get_200(user.login())
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return get_500("Login failed")


@auth.post("/register")
def register():
    try:
        email = request.form.get("email")
        password = request.form.get("password")
        username = request.form.get("username")
        tg_id = request.form.get("tg_id")

        mailer = EmailService()

        if not email or not password:
            return get_400("Email and password are required")
        
        user: User | None = User(email=email, password=generate_password_hash(password), username=username, tg_id=tg_id, auto_add=False)

        if user.get() is not None:
            return get_400("User already exists")
        
        user.add()
        token = Token(user_email=email, token_type=TokenTypes.VERIFY_EMAIL)
        token.add()

        mailer.send_verification_email(email, token.token)

        return get_200("Check your email for verification")
    except Exception as e:
        logger.error(f"Error in register: {e}")
        return get_500("Register failed")
    

@auth.post("/forgot-password")
def forgot_password():
    try:
        email = request.form.get("email")
        mailer = EmailService()

        if not email:
            return get_400("Email is required")
        
        user = User(email=email)
        if user.get() is None:
            return get_404("User not found")
        
        token = Token(user_email=email, token_type=TokenTypes.RESET_PASSWORD)
        token.add()

        mailer.send_password_reset_email(email, token.token)

        return get_200("Check your email for password reset")
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}")
        return get_500("Forgot password failed")


@auth.post("/verify_token")
def verify_token():
    try:
        email = request.form.get("email")
        token = request.form.get("verify_token")
        token_type = request.form.get("token_type")
        password = request.form.get("password")

        if not email or not token or not token_type:
            return get_400("Email, token and token type are required")
        
        token = Token(token=token, user_email=email, token_type=token_type)
        user = User(email=email)

        if token.get() is None:
            return get_400("Invalid token")

        if token.token_type == TokenTypes.VERIFY_EMAIL:
            if password is not None:
                return get_400("Password is not allowed for verify email token")
        
        if token.token_type == TokenTypes.RESET_PASSWORD:
            if password is None:
                return get_400("Password is required for reset password token")
            else:
                user.password = generate_password_hash(password)
        
        if token.expires_at < datetime.now():
            return get_400("Token expired")
        
        user.get()
        user.is_verified = True
        user.update()

        token.delete()

        return get_200(user.login())
    except Exception as e:
        logger.error(f"Error in verify_token: {e}")
        return get_500("Token verification failed")
