from flask import render_template, redirect, url_for
from app.presentation.main import main
from datetime import datetime

@main.route('/')
def index():
    """Landing page for the application."""
    return render_template('index.html', title='Welcome to Aspire', now=datetime.now())

@main.route('/about')
def about():
    """About page with information about the application."""
    return render_template('about.html', title='About Aspire', now=datetime.now())
