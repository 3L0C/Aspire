#!/usr/bin/env python3

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, FloatField, BooleanField, SubmitField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class TaskForm(FlaskForm):
    """Base form for creating/editing tasks."""
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    due_date = DateField('Due Date', validators=[Optional()], format='%Y-%m-%d')
    priority = SelectField('Priority',
                         choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
                         validators=[DataRequired()])
    estimated_duration = FloatField('Estimated Duration (hours)', validators=[Optional(), NumberRange(min=0)])
    related_goals = SelectMultipleField('Related Goals', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Task')


class OneTimeTaskForm(TaskForm):
    """Form for one-time tasks."""
    deadline = DateField('Deadline', validators=[Optional()], format='%Y-%m-%d')
    reminder = DateField('Reminder', validators=[Optional()], format='%Y-%m-%d')


class RecurringTaskForm(TaskForm):
    """Form for recurring tasks."""
    frequency = SelectField('Frequency',
                          choices=[('Daily', 'Daily'), ('Weekly', 'Weekly'),
                                  ('Monthly', 'Monthly'), ('Custom', 'Custom')],
                          validators=[DataRequired()])
    interval = IntegerField('Interval', validators=[Optional(), NumberRange(min=1)])
    end_date = DateField('End Date', validators=[Optional()], format='%Y-%m-%d')


class TaskLinkForm(FlaskForm):
    """Form for linking a task to a goal."""
    goal_id = SelectField('Goal', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Link Task')


class TaskCompleteForm(FlaskForm):
    """Form for marking a task as complete."""
    actual_duration = FloatField('Actual Duration (hours)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Mark Complete')
