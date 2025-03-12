#!/usr/bin/env python3

from datetime import datetime, timedelta
from app.data.models.goal import Goal, LongTermGoal, ShortTermGoal, MilestoneGoal
from app.data.models.task import Task, OneTimeTask, RecurringTask
from sqlalchemy import func, case, extract
from app.analytics.models import (
    AnalyticsResult, ProgressSnapshot, GoalAnalytics,
    TaskAnalytics, UserProductivityAnalytics
)
from app import db

class AnalyticsService:
    """Service for computing analytics on goals and tasks."""

    @staticmethod
    def get_user_dashboard_analytics(user_id):
        """Get overview analytics for user dashboard."""
        results = {}

        # Goal progress distribution
        results['goal_progress'] = AnalyticsService.get_goal_progress_distribution(user_id)

        # Task completion rate
        results['task_completion'] = AnalyticsService.get_task_completion_rate(user_id)

        # Progress over time
        results['progress_over_time'] = AnalyticsService.get_progress_over_time(user_id)

        # Task breakdown by priority
        results['task_by_priority'] = AnalyticsService.get_tasks_by_priority(user_id)

        # Productivity streak
        results['productivity_streak'] = AnalyticsService.get_productivity_streak(user_id)

        return results

    @staticmethod
    def get_goal_progress_distribution(user_id):
        """Get distribution of goal progress."""
        # Buckets for goal progress
        buckets = [
            (0, 20, '0-20%'),
            (21, 40, '21-40%'),
            (41, 60, '41-60%'),
            (61, 80, '61-80%'),
            (81, 99, '81-99%'),
            (100, 100, 'Completed')
        ]

        # Get all goals for the user
        goals = Goal.query.filter_by(user_id=user_id).all()

        # Count goals in each bucket
        distribution = {label: 0 for _, _, label in buckets}
        for goal in goals:
            for min_val, max_val, label in buckets:
                if min_val <= goal.progress <= max_val:
                    distribution[label] += 1
                    break

        # Create analytics result
        labels = [label for _, _, label in buckets]
        values = [distribution[label] for label in labels]

        return AnalyticsResult(
            title='Goal Progress Distribution',
            chart_type='pie',
            labels=labels,
            series=['Goals'],
            data=values,
            summary_stats={
                'total_goals': len(goals),
                'completed_goals': sum(1 for g in goals if g.is_completed),
                'in_progress_goals': sum(1 for g in goals if not g.is_completed),
                'average_progress': sum(g.progress for g in goals) / len(goals) if goals else 0
            }
        )

    @staticmethod
    def get_task_completion_rate(user_id):
        """Get task completion rate over time."""
        # Get completed tasks grouped by day for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Query completed tasks per day
        completed_tasks = db.session.query(
            func.date(Task.updated_at).label('date'),
            func.count().label('count')
        ).filter(
            Task.user_id == user_id,
            Task.is_completed == True,
            Task.updated_at >= thirty_days_ago
        ).group_by(
            func.date(Task.updated_at)
        ).all()

        # Create a dictionary with dates as keys
        completion_by_date = {str(row.date): row.count for row in completed_tasks}

        # Fill in missing dates
        dates = []
        counts = []
        current_date = thirty_days_ago.date()
        end_date = datetime.utcnow().date()

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            counts.append(completion_by_date.get(date_str, 0))
            current_date += timedelta(days=1)

        return AnalyticsResult(
            title='Task Completion Over Time',
            chart_type='line',
            labels=dates,
            series=['Completed Tasks'],
            data=[{'date': date, 'count': count} for date, count in zip(dates, counts)],
            summary_stats={
                'total_completed': sum(counts),
                'average_per_day': sum(counts) / len(counts) if counts else 0,
                'most_productive_day': dates[counts.index(max(counts))] if counts and max(counts) > 0 else None,
                'tasks_today': counts[-1] if counts else 0
            }
        )

    @staticmethod
    def get_progress_over_time(user_id):
        """Get overall progress over time."""
        # This is more complex as we'd need to track goal progress history
        # For now, use a simpler approach with current progress by goal type

        # Get goals by type
        long_term_goals = LongTermGoal.query.filter_by(user_id=user_id).all()
        short_term_goals = ShortTermGoal.query.filter(
            ShortTermGoal.user_id == user_id,
            ShortTermGoal.type == 'short_term'  # Exclude milestones
        ).all()
        milestones = MilestoneGoal.query.filter_by(user_id=user_id).all()

        # Calculate average progress for each type
        avg_progress = {
            'Long-term Goals': sum(g.progress for g in long_term_goals) / len(long_term_goals) if long_term_goals else 0,
            'Short-term Goals': sum(g.progress for g in short_term_goals) / len(short_term_goals) if short_term_goals else 0,
            'Milestones': sum(g.progress for g in milestones) / len(milestones) if milestones else 0
        }

        return AnalyticsResult(
            title='Progress by Goal Type',
            chart_type='bar',
            labels=list(avg_progress.keys()),
            series=['Average Progress (%)'],
            data=[avg_progress[key] for key in avg_progress.keys()],
            summary_stats={
                'total_goals': len(long_term_goals) + len(short_term_goals) + len(milestones),
                'long_term_count': len(long_term_goals),
                'short_term_count': len(short_term_goals),
                'milestone_count': len(milestones)
            }
        )

    @staticmethod
    def get_tasks_by_priority(user_id):
        """Get task breakdown by priority."""
        # Count tasks by priority
        tasks_by_priority = db.session.query(
            Task.priority,
            func.count().label('count')
        ).filter(
            Task.user_id == user_id
        ).group_by(
            Task.priority
        ).all()

        # Create result
        priorities = ['High', 'Medium', 'Low']
        counts = {priority: 0 for priority in priorities}

        for priority, count in tasks_by_priority:
            if priority in counts:
                counts[priority] = count

        return AnalyticsResult(
            title='Tasks by Priority',
            chart_type='pie',
            labels=priorities,
            series=['Tasks'],
            data=[counts[priority] for priority in priorities],
            summary_stats={
                'total_tasks': sum(counts.values()),
                'high_priority_percentage': (counts['High'] / sum(counts.values()) * 100) if sum(counts.values()) > 0 else 0
            }
        )

    @staticmethod
    def get_productivity_streak(user_id):
        """Get the user's productivity streak."""
        # Get dates with completed tasks
        completed_task_dates = db.session.query(
            func.date(Task.updated_at).label('date')
        ).filter(
            Task.user_id == user_id,
            Task.is_completed == True
        ).distinct().order_by(
            func.date(Task.updated_at)
        ).all()

        # Convert to list of dates
        completed_dates = [row.date for row in completed_task_dates]

        # Calculate current streak
        current_streak = 0
        current_date = datetime.utcnow().date()

        # Check yesterday first
        yesterday = current_date - timedelta(days=1)
        if yesterday not in completed_dates:
            # Streak broken if no tasks completed yesterday
            pass
        else:
            # Count backwards from yesterday
            check_date = yesterday
            while check_date in completed_dates:
                current_streak += 1
                check_date -= timedelta(days=1)

        # Check today
        if current_date in completed_dates:
            current_streak += 1

        # For a full implementation, we would calculate longest streak as well
        # This would require additional logic to find all streaks

        return AnalyticsResult(
            title='Productivity Streak',
            chart_type='value',  # Not a chart but a single value display
            data=current_streak,
            summary_stats={
                'current_streak': current_streak,
                'last_active_date': max(completed_dates) if completed_dates else None
            }
        )

    @staticmethod
    def get_goal_analytics(goal_id):
        """Get detailed analytics for a specific goal."""
        goal = Goal.query.get_or_404(goal_id)

        # Create goal analytics object
        analytics = GoalAnalytics(goal_id, goal.title)

        # Get basic stats
        analytics.completion_rate = goal.progress

        # Get related task stats
        total_tasks = len(goal.related_tasks)
        completed_tasks = sum(1 for t in goal.related_tasks if t.is_completed)

        analytics.related_task_stats = {
            'total': total_tasks,
            'completed': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'remaining': total_tasks - completed_tasks
        }

        # Get child goal stats if applicable
        child_goals = list(goal.child_goals)
        if child_goals:
            total_children = len(child_goals)
            completed_children = sum(1 for g in child_goals if g.is_completed)
            analytics.child_goal_stats = {
                'total': total_children,
                'completed': completed_children,
                'completion_rate': (completed_children / total_children * 100) if total_children > 0 else 0,
                'remaining': total_children - completed_children
            }

        # For progress over time, in a real implementation we would track progress history
        # For now, we'll create some synthetic data for demonstration
        if goal.start_date:
            days_since_start = (datetime.utcnow() - goal.start_date).days

            # Create synthetic progress snapshots
            # In a real implementation, we would store progress history in the database
            for i in range(min(5, max(1, days_since_start))):
                date = goal.start_date + timedelta(days=i * max(1, days_since_start // 5))
                # Create a realistic progression curve
                value = min(goal.progress * (i + 1) / 5, goal.progress)
                analytics.progress_over_time.append(ProgressSnapshot(date, value))

        # Add current progress as the last point
        analytics.progress_over_time.append(
            ProgressSnapshot(datetime.utcnow(), goal.progress)
        )

        return analytics

    @staticmethod
    def get_estimation_accuracy(user_id):
        """Calculate task estimation accuracy."""
        # Get tasks with both estimated and actual duration
        tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.is_completed == True,
            Task.estimated_duration.isnot(None),
            Task.actual_duration.isnot(None)
        ).all()

        if not tasks:
            return AnalyticsResult(
                title='Estimation Accuracy',
                chart_type='bar',
                labels=[],
                series=[],
                data=[],
                summary_stats={
                    'average_accuracy': 0,
                    'total_analyzed_tasks': 0
                }
            )

        # Calculate accuracy for each task
        accuracies = []
        for task in tasks:
            # Avoid division by zero
            if task.estimated_duration == 0:
                accuracy = 0
            else:
                # A perfect estimate would be 100%
                # Under-estimation would be < 100%
                # Over-estimation would be > 100%
                accuracy = (task.estimated_duration / task.actual_duration) * 100
            accuracies.append(accuracy)

        # Group into categories
        categories = [
            (0, 50, 'Severely Underestimated'),
            (50, 80, 'Underestimated'),
            (80, 120, 'Good Estimate'),
            (120, 150, 'Overestimated'),
            (150, float('inf'), 'Severely Overestimated')
        ]

        # Count tasks in each category
        category_counts = {label: 0 for _, _, label in categories}
        for accuracy in accuracies:
            for min_val, max_val, label in categories:
                if min_val <= accuracy < max_val:
                    category_counts[label] += 1
                    break

        # Prepare result
        labels = [label for _, _, label in categories]
        counts = [category_counts[label] for label in labels]

        return AnalyticsResult(
            title='Estimation Accuracy',
            chart_type='bar',
            labels=labels,
            series=['Tasks'],
            data=counts,
            summary_stats={
                'average_accuracy': sum(accuracies) / len(accuracies),
                'total_analyzed_tasks': len(tasks),
                'most_common_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
            }
        )
