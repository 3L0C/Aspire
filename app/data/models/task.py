#!/usr/bin/env python3
from app import db
from app.data.models.base import BaseEntity
from app.data.models.goal import Goal
from datetime import datetime, timedelta

class Task(BaseEntity):
    """Base class for all tasks."""
    __tablename__ = 'task'

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    priority = db.Column(db.String(20))  # High, Medium, Low
    is_completed = db.Column(db.Boolean, default=False)
    estimated_duration = db.Column(db.Float)  # In hours
    actual_duration = db.Column(db.Float)  # In hours
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Discriminator for inheritance
    type = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'task'
    }

    def mark_complete(self):
        """Mark the task as completed."""
        self.is_completed = True
        self.updated_at = datetime.utcnow()

        # Update related goals
        for goal in self.related_goals:
            goal.update_progress()

    def link_to_goal(self, goal):
        """Link this task to a goal."""
        if goal not in self.related_goals:
            self.related_goals.append(goal)

    def __repr__(self):
        return f'<Task {self.title}>'


class OneTimeTask(Task):
    """One-time tasks that occur only once."""
    __mapper_args__ = {
        'polymorphic_identity': 'one_time'
    }

    deadline = db.Column(db.DateTime)
    reminder = db.Column(db.DateTime)

    def calculate_time_left(self):
        """Calculate the time left until the deadline."""
        if not self.deadline:
            return None

        now = datetime.utcnow()
        if now > self.deadline:
            return timedelta(0)

        return self.deadline - now

    def set_reminder(self, hours_before=24):
        """Set a reminder for the task."""
        if self.deadline:
            self.reminder = self.deadline - timedelta(hours=hours_before)


class RecurringTask(Task):
    """Tasks that repeat on a schedule."""
    __mapper_args__ = {
        'polymorphic_identity': 'recurring'
    }

    frequency = db.Column(db.String(20))  # Daily, Weekly, Monthly, Custom
    interval = db.Column(db.Integer, default=1)  # e.g., every 2 weeks
    end_date = db.Column(db.DateTime)

    def generate_next_occurrence(self):
        """Generate the next occurrence of the task based on frequency."""
        if not self.due_date:
            return None

        if self.frequency == 'Daily':
            return self.due_date + timedelta(days=self.interval)
        elif self.frequency == 'Weekly':
            return self.due_date + timedelta(weeks=self.interval)
        elif self.frequency == 'Monthly':
            # Simple implementation - not accounting for month lengths
            new_month = self.due_date.month + self.interval
            new_year = self.due_date.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            return self.due_date.replace(year=new_year, month=new_month)

        return None

    def evaluate_completion_pattern(self):
        """Evaluate the completion pattern of the recurring task."""
        # This would require task history, which we can implement later
        return "Not implemented yet"
