#!/usr/bin/env python3

class ProgressSnapshot:
    """Represents a point-in-time progress snapshot for analytics."""

    def __init__(self, date, value, label=None):
        self.date = date
        self.value = value
        self.label = label

    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'value': self.value,
            'label': self.label
        }


class AnalyticsResult:
    """Container for analytics computation results."""

    def __init__(self,
                 title=None,
                 description=None,
                 data=None,
                 chart_type='bar',
                 labels=None,
                 series=None,
                 summary_stats=None):
        self.title = title
        self.description = description
        self.data = data if data is not None else []
        self.chart_type = chart_type  # bar, line, pie, radar, etc.
        self.labels = labels if labels is not None else []
        self.series = series if series is not None else []
        self.summary_stats = summary_stats if summary_stats is not None else {}

    def to_dict(self):
        result = {
            'title': self.title,
            'description': self.description,
            'chart_type': self.chart_type,
            'labels': self.labels,
            'series': self.series,
            'data': [d.to_dict() if hasattr(d, 'to_dict') else d for d in self.data],
            'summary_stats': self.summary_stats
        }
        return result


class GoalAnalytics:
    """Container for goal-specific analytics."""

    def __init__(self, goal_id, goal_title):
        self.goal_id = goal_id
        self.goal_title = goal_title
        self.progress_over_time = []
        self.completion_rate = 0.0
        self.time_to_complete = None
        self.related_task_stats = {}
        self.child_goal_stats = {}

    def to_dict(self):
        return {
            'goal_id': self.goal_id,
            'goal_title': self.goal_title,
            'progress_over_time': [p.to_dict() for p in self.progress_over_time],
            'completion_rate': self.completion_rate,
            'time_to_complete': self.time_to_complete,
            'related_task_stats': self.related_task_stats,
            'child_goal_stats': self.child_goal_stats
        }


class TaskAnalytics:
    """Container for task-specific analytics."""

    def __init__(self, task_id, task_title):
        self.task_id = task_id
        self.task_title = task_title
        self.completion_time = None
        self.estimated_vs_actual = None
        self.related_goals = []

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'task_title': self.task_title,
            'completion_time': self.completion_time,
            'estimated_vs_actual': self.estimated_vs_actual,
            'related_goals': self.related_goals
        }


class UserProductivityAnalytics:
    """Container for user productivity analytics."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.task_completion_rate = 0.0
        self.goal_progress_rate = 0.0
        self.productivity_by_day = {}
        self.productivity_by_category = {}
        self.streaks = {
            'current': 0,
            'longest': 0
        }

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'task_completion_rate': self.task_completion_rate,
            'goal_progress_rate': self.goal_progress_rate,
            'productivity_by_day': self.productivity_by_day,
            'productivity_by_category': self.productivity_by_category,
            'streaks': self.streaks
        }
