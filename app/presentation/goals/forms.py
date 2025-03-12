#!/usr/bin/env python3

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, FloatField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class GoalForm(FlaskForm):
    """Base form for creating/editing goals."""
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    start_date = DateField('Start Date', validators=[Optional()], format='%Y-%m-%d')
    target_date = DateField('Target Date', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Save Goal')


class LongTermGoalForm(GoalForm):
    """Form for long-term goals."""
    timeframe = StringField('Timeframe (e.g., "5 years")', validators=[Optional(), Length(max=50)])


class ShortTermGoalForm(GoalForm):
    """Form for short-term goals."""
    priority = SelectField('Priority',
                         choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
                         validators=[DataRequired()])
    difficulty = FloatField('Difficulty (1-10)', validators=[Optional(), NumberRange(min=1, max=10)])
    estimated_effort = FloatField('Estimated Effort (hours)', validators=[Optional(), NumberRange(min=0)])


class MilestoneGoalForm(ShortTermGoalForm):
    """Form for milestone goals."""
    parent_long_term_goal_id = SelectField('Parent Long-Term Goal', coerce=int, validators=[Optional()])
    sequence = IntegerField('Sequence', validators=[Optional(), NumberRange(min=1)])
    is_gateway = BooleanField('Is Gateway Milestone')


class GoalLinkForm(FlaskForm):
    """Form for linking a goal to a parent goal."""
    parent_goal_id = SelectField('Parent Goal', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Link Goal')
