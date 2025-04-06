#!/usr/bin/env python3

"""Unit tests for database models."""

import pytest
from app.data.models.user import User
from app.data.models.goal import Goal, LongTermGoal, ShortTermGoal, MilestoneGoal
from app.data.models.task import Task, OneTimeTask, RecurringTask


def test_user_password_hashing(app, _db):
    """Test password hashing works correctly."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')

        assert user.password_hash is not None
        assert user.password_hash != 'password'
        assert user.check_password('password') is True
        assert user.check_password('wrong-password') is False


def test_user_profile_creation(app, _db):
    """Test user profile is created correctly."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        _db.session.add(user)
        _db.session.commit()

        # Initially, profile should not exist
        assert user.profile is None

        # Create profile
        user.manage_profile()
        _db.session.commit()

        # Now profile should exist
        assert user.profile is not None
        assert user.profile.display_name == 'testuser'

        # Test preferences
        user.profile.update_preference('theme', 'dark')
        assert user.profile.preferences['theme'] == 'dark'


def test_goal_creation(app, _db, test_user):
    """Test goal creation and relationships."""
    with app.app_context():
        # Create a long-term goal
        long_term = LongTermGoal(
            title="Master Python",
            description="Become proficient in Python programming",
            user_id=test_user.id,
            timeframe="1 year"
        )
        _db.session.add(long_term)

        # Create a short-term goal
        short_term = ShortTermGoal(
            title="Complete Flask Tutorial",
            description="Work through the Flask mega-tutorial",
            user_id=test_user.id,
            priority="High",
            difficulty=7.5,
            estimated_effort=20
        )
        _db.session.add(short_term)
        _db.session.commit()

        # Link short-term goal to long-term goal
        short_term.link_to_goal(long_term)
        _db.session.commit()

        # Test relationships
        assert short_term in long_term.child_goals
        assert long_term in short_term.parent_goals

        # Test goal attributes
        assert long_term.timeframe == "1 year"
        assert short_term.priority == "High"
        assert short_term.difficulty == 7.5
        assert short_term.estimated_effort == 20


def test_task_creation(app, _db, test_user, test_goal):
    """Test task creation and relationships with goals."""
    with app.app_context():
        # Create a one-time task
        task = OneTimeTask(
            title="Complete Assignment",
            description="Finish the programming assignment",
            user_id=test_user.id,
            priority="High"
        )
        _db.session.add(task)
        _db.session.commit()

        # Retrieve a fresh copy of the goal from the current session before linking
        fresh_goal = Goal.query.get(test_goal.id)

        # Link task to goal using the fresh goal instance
        task.link_to_goal(fresh_goal)
        _db.session.commit()

        # Test relationships
        assert task in fresh_goal.related_tasks
        assert fresh_goal in task.related_goals

        # Test task completion
        assert task.is_completed is False
        task.mark_complete()
        _db.session.commit()

        # Test goal progress update
        fresh_goal = Goal.query.get(fresh_goal.id)  # Refresh again to see changes
        assert fresh_goal.progress > 0  # Progress should have increased
