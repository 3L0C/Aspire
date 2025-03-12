#!/usr/bin/env python3

from app import db
from app.data.models.base import BaseEntity
import json

class UserProfile(BaseEntity):
    """User profile with preferences and achievement stats."""
    __tablename__ = 'user_profile'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    display_name = db.Column(db.String(100))
    _preferences = db.Column(db.Text, default='{}')  # JSON string of preferences
    _achievement_stats = db.Column(db.Text, default='{}')  # JSON string of stats

    @property
    def preferences(self):
        return json.loads(self._preferences)

    @preferences.setter
    def preferences(self, value):
        self._preferences = json.dumps(value)

    @property
    def achievement_stats(self):
        return json.loads(self._achievement_stats)

    @achievement_stats.setter
    def achievement_stats(self, value):
        self._achievement_stats = json.dumps(value)

    def update_preference(self, key, value):
        """Update a specific preference."""
        prefs = self.preferences
        prefs[key] = value
        self.preferences = prefs

    def get_achievement_summary(self):
        """Get a summary of user achievements."""
        stats = self.achievement_stats
        return {
            'total_goals_completed': stats.get('total_goals_completed', 0),
            'total_tasks_completed': stats.get('total_tasks_completed', 0),
            'current_streak': stats.get('current_streak', 0),
            'longest_streak': stats.get('longest_streak', 0)
        }
