#!/usr/bin/env python3

"""Test configuration settings for the Aspire application."""

import os
import pytest
from app import create_app


def test_development_config():
    """Test development configuration."""
    app = create_app()
    assert app.config['DEBUG'] is not True
    assert app.config['TESTING'] is not True
    assert app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite:///:memory:'


def test_testing_config():
    """Test testing configuration."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    assert app.config['DEBUG'] is not True
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert app.config['WTF_CSRF_ENABLED'] is False
