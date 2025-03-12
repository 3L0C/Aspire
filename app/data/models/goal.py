#!/usr/bin/env python3

from app import db
from app.data.models.base import BaseEntity
from datetime import datetime

# Association table for goal-task relationship
goal_task_association = db.Table('goal_task_association',
    db.Column('goal_id', db.Integer, db.ForeignKey('goal.id'), primary_key=True),
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True)
)

# Association table for parent-child goal relationship
goal_hierarchy = db.Table('goal_hierarchy',
    db.Column('parent_id', db.Integer, db.ForeignKey('goal.id'), primary_key=True),
    db.Column('child_id', db.Integer, db.ForeignKey('goal.id'), primary_key=True)
)

class Goal(BaseEntity):
    """Base class for all goals."""
    __tablename__ = 'goal'

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_date = db.Column(db.DateTime)
    progress = db.Column(db.Float, default=0.0)  # 0-100 percentage
    is_completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    color = db.Column(db.String(7), default="#3498db")

    # Discriminator for inheritance
    type = db.Column(db.String(20))

    # Relationships
    related_tasks = db.relationship('Task', secondary=goal_task_association,
                                   backref=db.backref('related_goals', lazy='dynamic'))

    # Self-referential relationship for goal hierarchy
    parent_goals = db.relationship(
        'Goal', secondary=goal_hierarchy,
        primaryjoin="remote(goal_hierarchy.c.child_id) == Goal.id",
        secondaryjoin="remote(goal_hierarchy.c.parent_id) == Goal.id",
        backref=db.backref('child_goals', lazy='dynamic'),
        lazy='dynamic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'goal'
    }

    def calculate_progress(self):
        """Calculate progress based on related tasks and child goals."""
        # Simple implementation - can be enhanced later
        if self.is_completed:
            return 100.0

        task_progress = 0
        total_tasks = len(self.related_tasks)

        if total_tasks > 0:
            completed_tasks = sum(1 for task in self.related_tasks if task.is_completed)
            task_progress = (completed_tasks / total_tasks) * 100

        # Update progress
        self.progress = task_progress
        return self.progress

    def update_progress(self):
        """Update progress and check if completed."""
        self.progress = self.calculate_progress()
        if self.progress >= 100:
            self.is_completed = True
        db.session.add(self)

    def link_to_goal(self, parent_goal):
        """Link this goal as a child of another goal."""
        if parent_goal not in self.parent_goals:
            self.parent_goals.append(parent_goal)

    def __repr__(self):
        return f'<Goal {self.title}>'


class LongTermGoal(Goal):
    """Long-term goals that might span months or years."""
    __mapper_args__ = {
        'polymorphic_identity': 'long_term'
    }

    timeframe = db.Column(db.String(50))  # e.g., "5 years", "2 years"

    def add_milestone(self, milestone):
        """Add a milestone to this long-term goal."""
        if isinstance(milestone, MilestoneGoal):
            milestone.parent_long_term_goal_id = self.id
            self.child_goals.append(milestone)

    def evaluate_overall_progress(self):
        """Evaluate overall progress based on milestones."""
        milestone_count = self.child_goals.count()
        if milestone_count == 0:
            return self.progress

        total_progress = sum(goal.progress for goal in self.child_goals)
        return total_progress / milestone_count


class ShortTermGoal(Goal):
    """Short-term goals that can be achieved in days/weeks."""
    __mapper_args__ = {
        'polymorphic_identity': 'short_term'
    }

    priority = db.Column(db.String(20))  # High, Medium, Low
    difficulty = db.Column(db.Float)  # 1-10 scale
    estimated_effort = db.Column(db.Float)  # hours

    def calculate_feasibility(self):
        """Calculate feasibility based on difficulty and estimated effort."""
        # Simple implementation - can be enhanced
        if self.difficulty > 8 and self.estimated_effort > 40:
            return "Low"
        elif self.difficulty > 5 or self.estimated_effort > 20:
            return "Medium"
        else:
            return "High"


class MilestoneGoal(ShortTermGoal):
    """Milestone goals are significant achievements within a long-term goal."""
    __mapper_args__ = {
        'polymorphic_identity': 'milestone'
    }

    parent_long_term_goal_id = db.Column(db.Integer, db.ForeignKey('goal.id'))
    sequence = db.Column(db.Integer)  # Order in the milestone sequence
    is_gateway = db.Column(db.Boolean, default=False)  # Critical path milestone

    def update_parent_progress(self):
        """Update the progress of the parent long-term goal."""
        if self.parent_long_term_goal_id:
            parent = Goal.query.get(self.parent_long_term_goal_id)
            if parent:
                parent.update_progress()
                db.session.add(parent)
