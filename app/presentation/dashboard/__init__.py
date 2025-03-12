#!/usr/bin/env python3

from flask import Blueprint

dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from app.presentation.dashboard import routes
