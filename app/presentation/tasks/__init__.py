#!/usr/bin/env python3

from flask import Blueprint

tasks = Blueprint('tasks', __name__, url_prefix='/tasks')

from app.presentation.tasks import routes
