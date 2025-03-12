#!/usr/bin/env python3

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.presentation.tasks import tasks
from app.presentation.tasks.forms import (
    TaskForm, OneTimeTaskForm, RecurringTaskForm, TaskLinkForm, TaskCompleteForm
)
from app.data.models.task import Task, OneTimeTask, RecurringTask
from app.data.models.goal import Goal
from datetime import datetime

@tasks.route('/')
@login_required
def index():
    """Display all tasks."""
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks/index.html', tasks=user_tasks)

@tasks.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new task."""
    task_type = request.args.get('type', 'one_time')

    if task_type == 'recurring':
        form = RecurringTaskForm()
        task_class = RecurringTask
    else:  # default to one_time
        form = OneTimeTaskForm()
        task_class = OneTimeTask

    # Populate related goals field
    form.related_goals.choices = [
        (g.id, g.title)
        for g in Goal.query.filter_by(user_id=current_user.id).all()
    ]

    if form.validate_on_submit():
        task = task_class(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            estimated_duration=form.estimated_duration.data,
            user_id=current_user.id
        )

        # Set additional attributes based on task type
        if task_type == 'one_time':
            task.deadline = form.deadline.data
            task.reminder = form.reminder.data
        else:  # recurring
            task.frequency = form.frequency.data
            task.interval = form.interval.data
            task.end_date = form.end_date.data

        db.session.add(task)
        db.session.commit()

        # Link to related goals
        if form.related_goals.data:
            for goal_id in form.related_goals.data:
                goal = Goal.query.get(goal_id)
                if goal and goal.user_id == current_user.id:
                    task.link_to_goal(goal)

            db.session.commit()

        flash(f'Task "{task.title}" created successfully!')
        return redirect(url_for('tasks.index'))

    return render_template('tasks/create.html', form=form, task_type=task_type)

@tasks.route('/<int:id>')
@login_required
def view(id):
    """View task details."""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('tasks/view.html', task=task)

@tasks.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a task."""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if task.type == 'recurring':
        form = RecurringTaskForm(obj=task)
    else:  # one_time
        form = OneTimeTaskForm(obj=task)

    # Populate related goals field
    form.related_goals.choices = [
        (g.id, g.title)
        for g in Goal.query.filter_by(user_id=current_user.id).all()
    ]
    form.related_goals.data = [goal.id for goal in task.related_goals]

    if form.validate_on_submit():
        form.populate_obj(task)

        # Update related goals
        task.related_goals = []
        if form.related_goals.data:
            for goal_id in form.related_goals.data:
                goal = Goal.query.get(goal_id)
                if goal and goal.user_id == current_user.id:
                    task.link_to_goal(goal)

        db.session.commit()
        flash(f'Task "{task.title}" updated successfully!')
        return redirect(url_for('tasks.view', id=task.id))

    return render_template('tasks/edit.html', form=form, task=task)

@tasks.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a task."""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    title = task.title

    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{title}" deleted successfully!')

    return redirect(url_for('tasks.index'))

@tasks.route('/<int:id>/link', methods=['GET', 'POST'])
@login_required
def link(id):
    """Link a task to a goal."""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    form = TaskLinkForm()
    form.goal_id.choices = [
        (g.id, g.title)
        for g in Goal.query.filter_by(user_id=current_user.id).all()
    ]

    if form.validate_on_submit():
        goal = Goal.query.get(form.goal_id.data)
        if goal and goal.user_id == current_user.id:
            task.link_to_goal(goal)
            db.session.commit()
            flash(f'Task "{task.title}" linked to "{goal.title}" successfully!')
            return redirect(url_for('tasks.view', id=task.id))

    return render_template('tasks/link.html', form=form, task=task)

@tasks.route('/<int:id>/complete', methods=['GET', 'POST'])
@login_required
def complete(id):
    """Mark a task as complete."""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if task.is_completed:
        flash('This task is already completed.')
        return redirect(url_for('tasks.view', id=task.id))

    form = TaskCompleteForm()

    if form.validate_on_submit() or request.method == 'POST':
        task.actual_duration = form.actual_duration.data
        task.mark_complete()
        db.session.commit()
        flash(f'Task "{task.title}" marked as complete!')

        # If recurring task, generate next occurrence
        if task.type == 'recurring':
            next_due_date = task.generate_next_occurrence()
            if next_due_date and (not task.end_date or next_due_date <= task.end_date):
                new_task = RecurringTask(
                    title=task.title,
                    description=task.description,
                    due_date=next_due_date,
                    priority=task.priority,
                    estimated_duration=task.estimated_duration,
                    user_id=current_user.id,
                    frequency=task.frequency,
                    interval=task.interval,
                    end_date=task.end_date
                )

                db.session.add(new_task)

                # Link to the same goals
                for goal in task.related_goals:
                    new_task.link_to_goal(goal)

                db.session.commit()
                flash(f'Next occurrence of "{task.title}" has been created.')

        return redirect(url_for('tasks.index'))

    return render_template('tasks/complete.html', form=form, task=task)

@tasks.route('/<int:id>/incomplete', methods=['POST'])
@login_required
def mark_incomplete(id):
    """Mark a task as incomplete."""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if not task.is_completed:
        flash('This task is already marked as incomplete.')
        return redirect(url_for('tasks.view', id=task.id))

    task.is_completed = False
    task.actual_duration = None  # Clear the actual duration
    db.session.commit()
    flash(f'Task "{task.title}" marked as incomplete!')

    return redirect(url_for('tasks.view', id=task.id))
