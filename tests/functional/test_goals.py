#!/usr/bin/env python3

"""Functional tests for goal management."""

from datetime import datetime, timedelta
from app.data.models.goal import Goal, LongTermGoal


def test_goals_page(auth_client):
    """Test that the goals page loads correctly."""
    response = auth_client.get('/goals/')
    assert response.status_code == 200
    assert b'My Goals' in response.data


def test_create_goal(auth_client, app):
    """Test goal creation functionality."""
    # Test creating a long-term goal
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    future = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

    response = auth_client.post(
        '/goals/create?type=long_term',
        data={
            'title': 'New Long-term Goal',
            'description': 'This is a test long-term goal',
            'start_date': tomorrow,
            'target_date': future,
            'timeframe': '1 year'
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'New Long-term Goal' in response.data
    assert b'created successfully' in response.data

    # Verify the goal exists in the database
    with app.app_context():
        goal = LongTermGoal.query.filter_by(title='New Long-term Goal').first()
        assert goal is not None
        assert goal.description == 'This is a test long-term goal'
        assert goal.timeframe == '1 year'


def test_view_goal(auth_client, test_goal):
    """Test viewing a specific goal."""
    response = auth_client.get(f'/goals/{test_goal.id}')
    assert response.status_code == 200
    assert test_goal.title.encode() in response.data

    # Check for expected elements
    assert b'Progress' in response.data
    assert b'Goal Details' in response.data


def test_edit_goal(auth_client, test_goal, app):
    """Test editing a goal."""
    # Get the edit page
    response = auth_client.get(f'/goals/{test_goal.id}/edit')
    assert response.status_code == 200
    assert b'Edit Goal' in response.data

    # Edit the goal
    new_title = 'Updated Goal Title'
    response = auth_client.post(
        f'/goals/{test_goal.id}/edit',
        data={
            'title': new_title,
            'description': test_goal.description,
            'timeframe': '2 years'  # Changed from 1 year
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert new_title.encode() in response.data
    assert b'updated successfully' in response.data

    # Verify the changes in the database
    with app.app_context():
        updated_goal = Goal.query.get(test_goal.id)
        assert updated_goal.title == new_title
        assert updated_goal.timeframe == '2 years'


def test_delete_goal(auth_client, test_goal, app):
    """Test deleting a goal."""
    response = auth_client.post(
        f'/goals/{test_goal.id}/delete',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'deleted successfully' in response.data

    # Verify the goal is removed from the database
    with app.app_context():
        goal = Goal.query.get(test_goal.id)
        assert goal is None


def test_update_goal_progress(auth_client, test_goal, app):
    """Test updating a goal's progress."""
    # Make the API request to update progress
    response = auth_client.post(
        f'/goals/{test_goal.id}/progress',
        data={'progress': '50'},
        follow_redirects=True
    )

    # Verify the request was successful
    assert response.status_code == 200

    # Verify the goal progress was updated in the database
    with app.app_context():
        from app.data.models.goal import Goal
        updated_goal = Goal.query.get(test_goal.id)
        assert updated_goal.progress == 50
