#!/usr/bin/env python3

from flask import Blueprint

goals = Blueprint('goals', __name__, url_prefix='/goals')

from app.presentation.goals import routes
