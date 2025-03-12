#!/usr/bin/env python3

from flask import jsonify, render_template, redirect, request, url_for
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

@dashboard.route('/api/goal-network')
@login_required
def api_goal_network():
    """API endpoint for goal network visualization data."""
    goals = Goal.query.filter_by(user_id=current_user.id).all()

    # Check if tasks should be included
    include_tasks = request.args.get('include_tasks', 'false').lower() == 'true'

    # Prepare data for network visualization
    nodes = []
    edges = []

    # Track processed nodes to avoid duplicates
    processed_nodes = set()

    # Create nodes for each goal
    for goal in goals:
        # Skip if already processed
        if goal.id in processed_nodes:
            continue

        processed_nodes.add(goal.id)

        # Determine node color based on goal type
        color = "#3498db"  # Default blue
        if goal.type == 'long_term':
            color = "#8e44ad"  # Purple
        elif goal.type == 'short_term':
            color = "#2ecc71"  # Green
        elif goal.type == 'milestone':
            color = "#f39c12"  # Orange

        # Determine size based on importance/progress
        size = 25 + (goal.progress / 4)  # Slightly larger base size

        # Format the label for better display
        display_label = goal.title
        if len(display_label) > 20:
            # For very long titles, truncate with ellipsis
            display_label = display_label[:17] + '...'

        # Create node with full information in tooltip
        tooltip = f"{goal.title}<br>Type: {goal.type.replace('_', ' ').title()}<br>Progress: {goal.progress:.1f}%"
        if goal.target_date:
            tooltip += f"<br>Target: {goal.target_date.strftime('%Y-%m-%d')}"

        nodes.append({
            'id': goal.id,
            'label': display_label,
            'title': tooltip,  # HTML tooltip
            'color': color,
            'size': size,
            'shape': 'box',  # Use box shape for better text display
            'progress': goal.progress,
            'type': goal.type,
            'is_completed': goal.is_completed
        })

    # Create edges for parent-child relationships
    for goal in goals:
        for child in goal.child_goals:
            edges.append({
                'from': goal.id,
                'to': child.id,
                'arrows': 'to',
                'title': 'Parent → Child'
            })

    # Add task nodes and edges if requested
    if include_tasks:
        # Get all tasks for this user to avoid duplicates when the same task is related to multiple goals
        processed_task_ids = set()

        for goal in goals:
            for task in goal.related_tasks:
                # Create a unique ID for task nodes
                task_id = f"task_{task.id}"

                # Skip if already processed this task
                if task_id in processed_task_ids:
                    # Still create the edge between this goal and the task
                    edges.append({
                        'from': goal.id,
                        'to': task_id,
                        'arrows': 'to',
                        'dashes': True,  # Dashed lines for goal-task connections
                        'title': 'Goal → Task'
                    })
                    continue

                processed_task_ids.add(task_id)

                # Determine task color based on priority
                task_color = "#e74c3c"  # Default red
                if task.priority == 'Medium':
                    task_color = "#f39c12"  # Orange
                elif task.priority == 'Low':
                    task_color = "#3498db"  # Blue

                # Determine size based on estimated duration
                task_size = 15
                if task.estimated_duration:
                    # Scale size based on duration, but keep it smaller than goals
                    task_size = min(15 + (task.estimated_duration / 2), 25)

                # Create task node
                tooltip = f"{task.title}<br>Priority: {task.priority}"
                if task.due_date:
                    tooltip += f"<br>Due: {task.due_date.strftime('%Y-%m-%d')}"
                if task.is_completed:
                    tooltip += "<br>Status: Completed"

                # Truncate task title if too long
                display_label = task.title
                if len(display_label) > 15:
                    display_label = display_label[:12] + '...'

                nodes.append({
                    'id': task_id,
                    'label': display_label,
                    'title': tooltip,
                    'color': task_color,
                    'size': task_size,
                    'shape': 'circle',  # Use circle shape for tasks
                    'font': {
                        'size': 10  # Smaller font for tasks
                    },
                    'borderWidth': task.is_completed and 3 or 1,  # Thicker border for completed tasks
                    'type': 'task',
                    'is_completed': task.is_completed
                })

                # Create edge from goal to task
                edges.append({
                    'from': goal.id,
                    'to': task_id,
                    'arrows': 'to',
                    'dashes': True,  # Dashed lines for goal-task connections
                    'title': 'Goal → Task'
                })

    return jsonify({
        'nodes': nodes,
        'edges': edges
    })
