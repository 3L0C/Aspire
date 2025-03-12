from flask import render_template, redirect, url_for, flash, request
from app.presentation.main import main
from datetime import datetime
from flask_login import login_required, current_user
from app import db
from app.data.models.user_profile import UserProfile

@main.route('/')
def index():
    """Landing page for the application."""
    return render_template('index.html', title='Welcome to Aspire', now=datetime.now())

@main.route('/about')
def about():
    """About page with information about the application."""
    return render_template('about.html', title='About Aspire', now=datetime.now())

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    # Ensure user has a profile
    if not current_user.profile:
        current_user.manage_profile()
        db.session.commit()

    if request.method == 'POST':
        # Handle display name update
        if 'display_name' in request.form:
            current_user.profile.display_name = request.form['display_name']

            # Update preferences
            preferences = current_user.profile.preferences

            # Theme preference
            if 'theme' in request.form:
                preferences['theme'] = request.form['theme']

            # Dashboard preferences
            if 'default_view' in request.form:
                preferences['default_view'] = request.form['default_view']

            # Due date reminder setting
            if 'reminder_days' in request.form:
                try:
                    preferences['reminder_days'] = int(request.form['reminder_days'])
                except ValueError:
                    pass

            # Update the preferences
            current_user.profile.preferences = preferences
            db.session.commit()

            flash('Settings updated successfully!', 'success')
            return redirect(url_for('main.settings'))

    # Get current preferences
    preferences = current_user.profile.preferences

    return render_template('settings.html',
                         title='User Settings',
                         now=datetime.now(),
                         preferences=preferences)
