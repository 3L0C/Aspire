#!/usr/bin/env python3

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.presentation.goals import goals
from app.presentation.goals.forms import (
    GoalForm, LongTermGoalForm, ShortTermGoalForm, MilestoneGoalForm, GoalLinkForm
)
from app.data.models.goal import Goal, LongTermGoal, ShortTermGoal, MilestoneGoal

@goals.route('/')
@login_required
def index():
    """Display all goals."""
    user_goals = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template('goals/index.html', goals=user_goals)

@goals.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new goal."""
    goal_type = request.args.get('type', 'short_term')

    if goal_type == 'long_term':
        form = LongTermGoalForm()
        goal_class = LongTermGoal
    elif goal_type == 'milestone':
        form = MilestoneGoalForm()
        goal_class = MilestoneGoal
        # Populate parent goal choices
        form.parent_long_term_goal_id.choices = [
            (g.id, g.title)
            for g in LongTermGoal.query.filter_by(user_id=current_user.id).all()
        ]
    else:  # default to short_term
        form = ShortTermGoalForm()
        goal_class = ShortTermGoal

    if form.validate_on_submit():
        goal = goal_class(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            target_date=form.target_date.data,
            user_id=current_user.id,
            color=form.color.data
        )

        # Set additional attributes based on goal type
        if goal_type == 'long_term':
            goal.timeframe = form.timeframe.data
        elif goal_type == 'short_term' or goal_type == 'milestone':
            goal.priority = form.priority.data
            goal.difficulty = form.difficulty.data
            goal.estimated_effort = form.estimated_effort.data

            if goal_type == 'milestone':
                goal.parent_long_term_goal_id = form.parent_long_term_goal_id.data
                goal.sequence = form.sequence.data
                goal.is_gateway = form.is_gateway.data

        db.session.add(goal)
        db.session.commit()
        flash(f'Goal "{goal.title}" created successfully!')
        return redirect(url_for('goals.index'))

    return render_template('goals/create.html', form=form, goal_type=goal_type)

@goals.route('/<int:id>')
@login_required
def view(id):
    """View goal details."""
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('goals/view.html', goal=goal)

@goals.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a goal."""
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if goal.type == 'long_term':
        form = LongTermGoalForm(obj=goal)
    elif goal.type == 'milestone':
        form = MilestoneGoalForm(obj=goal)
        form.parent_long_term_goal_id.choices = [
            (g.id, g.title)
            for g in LongTermGoal.query.filter_by(user_id=current_user.id).all()
        ]
    else:  # short_term
        form = ShortTermGoalForm(obj=goal)

    if form.validate_on_submit():
        form.populate_obj(goal)
        db.session.commit()
        flash(f'Goal "{goal.title}" updated successfully!')
        return redirect(url_for('goals.view', id=goal.id))

    return render_template('goals/edit.html', form=form, goal=goal)

@goals.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a goal."""
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    title = goal.title

    db.session.delete(goal)
    db.session.commit()
    flash(f'Goal "{title}" deleted successfully!')

    return redirect(url_for('goals.index'))

@goals.route('/<int:id>/link', methods=['GET', 'POST'])
@login_required
def link(id):
    """Link a goal to a parent goal."""
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    form = GoalLinkForm()
    # Exclude the current goal from potential parents
    form.parent_goal_id.choices = [
        (g.id, g.title)
        for g in Goal.query.filter_by(user_id=current_user.id).all()
        if g.id != goal.id
    ]

    if form.validate_on_submit():
        parent_goal = Goal.query.get(form.parent_goal_id.data)
        if parent_goal:
            goal.link_to_goal(parent_goal)
            db.session.commit()
            flash(f'Goal "{goal.title}" linked to "{parent_goal.title}" successfully!')
            return redirect(url_for('goals.view', id=goal.id))

    return render_template('goals/link.html', form=form, goal=goal)

@goals.route('/<int:id>/progress', methods=['POST'])
@login_required
def update_progress(id):
    """Update goal progress manually."""
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    progress = request.form.get('progress', type=float)
    is_completed = request.form.get('is_completed') == 'true'

    if progress is not None and 0 <= progress <= 100:
        goal.progress = progress

        # Allow manual completion status control
        goal.is_completed = is_completed

        db.session.commit()
        completion_status = "completed" if is_completed else "in progress"
        flash(f'Goal "{goal.title}" updated to {progress}% and marked as {completion_status}')

    return redirect(url_for('goals.view', id=goal.id))
