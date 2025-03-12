from flask import Blueprint

main = Blueprint('main', __name__)

from app.presentation.main import routes
