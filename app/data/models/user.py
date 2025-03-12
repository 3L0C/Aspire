#!/usr/bin/env python3

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.data.models.base import BaseEntity
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, BaseEntity):
    __tablename__ = 'user'

    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    # Relationships
    profile = db.relationship('UserProfile', uselist=False, backref='user', cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def authenticate(self):
        """Authenticate the user."""
        return True

    def manage_profile(self):
        """Create user profile if it doesn't exist."""
        if not self.profile:
            from app.data.models.user_profile import UserProfile
            self.profile = UserProfile(display_name=self.username)
            db.session.add(self.profile)

    def __repr__(self):
        return f'<User {self.username}>'
