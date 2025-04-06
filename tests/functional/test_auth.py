#!/usr/bin/env python3

"""Functional tests for authentication functionality."""

import pytest
from flask import session, g


def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data
    assert b'Username' in response.data
    assert b'Password' in response.data


def test_registration(client, app):
    """Test user registration functionality."""
    # Get the registration page
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

    # Register a new user
    response = client.post(
        '/register',
        data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword',
            'password2': 'newpassword'
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Congratulations, you are now a registered user!' in response.data

    # Verify the user exists in the database
    with app.app_context():
        from app.data.models.user import User
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'
        assert user.check_password('newpassword') is True


def test_login_logout(client, test_user):
    """Test login and logout functionality."""
    # Test login with correct credentials
    response = client.post(
        '/login',
        data={
            'username': 'testuser',
            'password': 'password',
            'remember_me': False
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Aspire' in response.data

    # Test accessing a protected page
    response = client.get('/dashboard/')
    assert response.status_code == 200

    # Test logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome to Aspire' in response.data

    # After logout, should not be able to access protected pages
    response = client.get('/dashboard/')
    assert response.status_code == 302  # Should redirect to login page


def test_invalid_login(client):
    """Test login with invalid credentials."""
    response = client.post(
        '/login',
        data={
            'username': 'testuser',
            'password': 'wrongpassword',
            'remember_me': False
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_register_validation(client, test_user):
    """Test registration form validation."""
    # Test duplicate username
    response = client.post(
        '/register',
        data={
            'username': 'testuser',  # This username already exists from fixture
            'email': 'another@example.com',
            'password': 'password',
            'password2': 'password'
        },
        follow_redirects=False  # Don't follow redirects to see validation errors
    )
    assert response.status_code == 200
    assert b'Please use a different username' in response.data

    # Test duplicate email
    response = client.post(
        '/register',
        data={
            'username': 'anotheruser',
            'email': 'test@example.com',  # This email already exists from fixture
            'password': 'password',
            'password2': 'password'
        },
        follow_redirects=False  # Don't follow redirects to see validation errors
    )
    assert response.status_code == 200
    assert b'Please use a different email address' in response.data

    # Test password mismatch
    response = client.post(
        '/register',
        data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password1',
            'password2': 'password2'  # Doesn't match
        },
        follow_redirects=False  # Don't follow redirects to see validation errors
    )
    assert response.status_code == 200
    assert b'Field must be equal to password' in response.data
