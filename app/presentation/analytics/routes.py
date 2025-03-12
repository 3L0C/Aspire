#!/usr/bin/env python3

from flask import render_template, jsonify, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.presentation.analytics import analytics
from app.analytics.services import AnalyticsService
from app.data.models.goal import Goal
from app.data.models.task import Task
from datetime import datetime
import traceback

@analytics.route('/')
@login_required
def index():
    """Main analytics dashboard view."""
    try:
        # Get analytics data for the dashboard
        analytics_data = AnalyticsService.get_user_dashboard_analytics(current_user.id)

        return render_template(
            'analytics/index.html',
            title='Analytics Dashboard',
            analytics_data=analytics_data
        )
    except Exception as e:
        current_app.logger.error(f"Error in analytics dashboard: {str(e)}\n{traceback.format_exc()}")
        flash(f"An error occurred while loading analytics: {str(e)}", "danger")
        return redirect(url_for('dashboard.index'))

@analytics.route('/goals')
@login_required
def goals_overview():
    """Goals overview analytics."""
    try:
        # Get goal progress distribution
        goal_progress = AnalyticsService.get_goal_progress_distribution(current_user.id)

        # Get progress over time
        progress_over_time = AnalyticsService.get_progress_over_time(current_user.id)

        # Get all goals for selection
        goals = Goal.query.filter_by(user_id=current_user.id).all()

        return render_template(
            'analytics/goals_overview.html',
            title='Goal Analytics',
            goal_progress=goal_progress,
            progress_over_time=progress_over_time,
            goals=goals
        )
    except Exception as e:
        current_app.logger.error(f"Error in goals overview: {str(e)}\n{traceback.format_exc()}")
        flash(f"An error occurred while loading goal analytics: {str(e)}", "danger")
        return redirect(url_for('analytics.index'))

@analytics.route('/goal/<int:goal_id>')
@login_required
def goal_detail(goal_id):
    """Detailed analytics for a specific goal."""
    try:
        # Ensure the goal belongs to the current user
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()

        # Get detailed analytics for the goal
        goal_analytics = AnalyticsService.get_goal_analytics(goal_id)

        # Ensure all required properties exist with defaults
        if not hasattr(goal_analytics, 'progress_over_time') or goal_analytics.progress_over_time is None:
            goal_analytics.progress_over_time = []

        if not hasattr(goal_analytics, 'related_task_stats') or goal_analytics.related_task_stats is None:
            goal_analytics.related_task_stats = {
                'total': 0,
                'completed': 0,
                'remaining': 0,
                'completion_rate': 0
            }

        if not hasattr(goal_analytics, 'child_goal_stats') or goal_analytics.child_goal_stats is None:
            goal_analytics.child_goal_stats = {
                'total': 0,
                'completed': 0,
                'remaining': 0,
                'completion_rate': 0
            }

        # Verify that all items in progress_over_time have date and value attributes
        for item in goal_analytics.progress_over_time:
            if not hasattr(item, 'date'):
                item.date = datetime.now()
            if not hasattr(item, 'value'):
                item.value = 0

        return render_template(
            'analytics/goal_detail.html',
            title=f'Analytics for {goal.title}',
            goal=goal,
            analytics=goal_analytics,
            now=datetime.now()
        )
    except Exception as e:
        current_app.logger.error(f"Error in goal detail: {str(e)}\n{traceback.format_exc()}")
        flash(f"An error occurred while loading goal analytics: {str(e)}", "danger")
        return redirect(url_for('analytics.goals_overview'))

@analytics.route('/tasks')
@login_required
def tasks_overview():
    """Tasks overview analytics."""
    try:
        # Get task completion rate
        task_completion = AnalyticsService.get_task_completion_rate(current_user.id)

        # Get tasks by priority
        tasks_by_priority = AnalyticsService.get_tasks_by_priority(current_user.id)

        # Get estimation accuracy
        estimation_accuracy = AnalyticsService.get_estimation_accuracy(current_user.id)

        return render_template(
            'analytics/tasks_overview.html',
            title='Task Analytics',
            task_completion=task_completion,
            tasks_by_priority=tasks_by_priority,
            estimation_accuracy=estimation_accuracy
        )
    except Exception as e:
        current_app.logger.error(f"Error in tasks overview: {str(e)}\n{traceback.format_exc()}")
        flash(f"An error occurred while loading task analytics: {str(e)}", "danger")
        return redirect(url_for('analytics.index'))

@analytics.route('/productivity')
@login_required
def productivity():
    """User productivity analytics."""
    try:
        # Get productivity streak
        streak = AnalyticsService.get_productivity_streak(current_user.id)

        # For a more complete implementation, we would include more productivity metrics

        return render_template(
            'analytics/productivity.html',
            title='Productivity Analytics',
            streak=streak
        )
    except Exception as e:
        current_app.logger.error(f"Error in productivity: {str(e)}\n{traceback.format_exc()}")
        flash(f"An error occurred while loading productivity analytics: {str(e)}", "danger")
        return redirect(url_for('analytics.index'))

@analytics.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard analytics data."""
    try:
        analytics_data = AnalyticsService.get_user_dashboard_analytics(current_user.id)

        # Convert to JSON-serializable format
        result = {}
        for key, value in analytics_data.items():
            if hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value

        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in API dashboard data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@analytics.route('/api/goal/<int:goal_id>')
@login_required
def api_goal_analytics(goal_id):
    """API endpoint for goal analytics data."""
    try:
        # Ensure the goal belongs to the current user
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()

        # Get detailed analytics
        goal_analytics = AnalyticsService.get_goal_analytics(goal_id)

        # Convert to dictionary with defaults for missing attributes
        result = {
            'goal_id': goal_analytics.goal_id,
            'goal_title': goal_analytics.goal_title,
            'progress_over_time': [],
            'completion_rate': getattr(goal_analytics, 'completion_rate', 0),
            'time_to_complete': getattr(goal_analytics, 'time_to_complete', None),
            'related_task_stats': getattr(goal_analytics, 'related_task_stats', {}),
            'child_goal_stats': getattr(goal_analytics, 'child_goal_stats', {})
        }

        # Process progress_over_time safely
        if hasattr(goal_analytics, 'progress_over_time') and goal_analytics.progress_over_time:
            for item in goal_analytics.progress_over_time:
                if hasattr(item, 'to_dict'):
                    result['progress_over_time'].append(item.to_dict())
                else:
                    # Create a safe dict version
                    result['progress_over_time'].append({
                        'date': item.date.isoformat() if hasattr(item, 'date') and item.date else None,
                        'value': item.value if hasattr(item, 'value') else 0,
                        'label': item.label if hasattr(item, 'label') else None
                    })

        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in API goal analytics: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
