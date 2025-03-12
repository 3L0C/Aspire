#!/usr/bin/env python3

from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.presentation.dashboard import dashboard
from app.data.models.goal import Goal, LongTermGoal, ShortTermGoal
from app.data.models.task import Task
from app.analytics.services import AnalyticsService
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

@dashboard.route('/')
@login_required
def index():
    """Main dashboard view."""
    # Get user's goals
    long_term_goals = LongTermGoal.query.filter_by(user_id=current_user.id).all()
    short_term_goals = ShortTermGoal.query.filter_by(user_id=current_user.id).all()

    # Get user's tasks
    today = datetime.now().date()
    upcoming_tasks = Task.query.filter(
        and_(
            Task.user_id == current_user.id,
            Task.is_completed == False,
            or_(
                Task.due_date >= today,
                Task.due_date == None
            )
        )
    ).order_by(Task.due_date).limit(10).all()

    # Calculate overall progress
    total_goals = len(long_term_goals) + len(short_term_goals)
    completed_goals = sum(1 for g in long_term_goals + short_term_goals if g.is_completed)
    overall_progress = (completed_goals / total_goals * 100) if total_goals > 0 else 0

    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, is_completed=True).count()
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Get recently completed tasks
    recent_completed_tasks = Task.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(Task.updated_at.desc()).limit(5).all()

    # Get analytics data for widget
    streak_data = AnalyticsService.get_productivity_streak(current_user.id).data

    return render_template(
        'dashboard/index.html',
        long_term_goals=long_term_goals,
        short_term_goals=short_term_goals,
        upcoming_tasks=upcoming_tasks,
        overall_progress=overall_progress,
        task_completion_rate=task_completion_rate,
        recent_completed_tasks=recent_completed_tasks,
        streak_data=streak_data
    )

@dashboard.route('/overview')
@login_required
def overview():
    """Overview of all goals and their relationships."""
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/overview.html', goals=goals)

@dashboard.route('/quick-add-task', methods=['GET', 'POST'])
@login_required
def quick_add_task():
    """Add a task quickly from the dashboard."""
    from app.presentation.tasks.forms import TaskForm
    from app.data.models.task import OneTimeTask
    from flask import request, flash
    from app import db

    form = TaskForm()

    if form.validate_on_submit():
        task = OneTimeTask(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            estimated_duration=form.estimated_duration.data,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()
        flash(f'Task "{task.title}" created successfully!')
        return redirect(url_for('dashboard.index'))

    return render_template('dashboard/quick_add_task.html', form=form)
