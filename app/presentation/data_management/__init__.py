#!/usr/bin/env python3

from flask import Blueprint

data_management = Blueprint('data_management', __name__, url_prefix='/data')

from app.presentation.data_management import routes
