#!/usr/bin/env python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    # Initialize Flask
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aspire.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.presentation.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.presentation.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.presentation.dashboard import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)

    from app.presentation.goals import goals as goals_blueprint
    app.register_blueprint(goals_blueprint)

    from app.presentation.tasks import tasks as tasks_blueprint
    app.register_blueprint(tasks_blueprint)

    from app.presentation.analytics import analytics as analytics_blueprint
    app.register_blueprint(analytics_blueprint)

    from app.presentation.data_management import data_management as data_management_blueprint
    app.register_blueprint(data_management_blueprint)

    # Set up URL routes
    @app.route('/')
    def index():
        return main_blueprint.index()

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create a default user if none exists
        from app.data.models.user import User
        if not User.query.filter_by(username='demo').first():
            default_user = User(username='demo', email='demo@example.com')
            default_user.set_password('password')
            db.session.add(default_user)
            db.session.commit()
            print("Created default user: demo / password")

    # Register context processors
    from app.context_processors import inject_now
    app.context_processor(inject_now)

    app.jinja_env.add_extension('jinja2.ext.do')

    return app
