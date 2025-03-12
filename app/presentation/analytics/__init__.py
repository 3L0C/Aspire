#!/usr/bin/env python3

from flask import Blueprint

analytics = Blueprint('analytics', __name__, url_prefix='/analytics')

from app.presentation.analytics import routes
