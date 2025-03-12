from flask import Blueprint

auth = Blueprint('auth', __name__)

from app.presentation.auth import routes
