#!/usr/bin/env python3

import json
import csv
import io
from datetime import datetime
from app import db
from app.data.models.user import User
from app.data.models.goal import Goal, LongTermGoal, ShortTermGoal, MilestoneGoal
from app.data.models.task import Task, OneTimeTask, RecurringTask
from flask import current_app
import os

class ImportExportService:
    """Service for importing and exporting user data."""

    @staticmethod
    def export_data(user_id, format='json'):
        """
        Export all user data to the specified format.

        Args:
            user_id: The ID of the user whose data to export
            format: 'json' or 'csv'

        Returns:
            tuple: (data, filename, mimetype)
        """
        # Get user data
        user = User.query.get(user_id)
        if not user:
            return None, None, None

        # Get all goals
        goals = Goal.query.filter_by(user_id=user_id).all()

        # Get all tasks
        tasks = Task.query.filter_by(user_id=user_id).all()

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"aspire_export_{user.username}_{timestamp}"

        if format == 'json':
            # Create export data structure
            export_data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'username': user.username,
                    'app_version': '1.0',
                },
                'goals': [ImportExportService._serialize_goal(goal) for goal in goals],
                'tasks': [ImportExportService._serialize_task(task) for task in tasks],
            }

            # Convert to JSON string
            data = json.dumps(export_data, indent=2)
            mimetype = 'application/json'
            filename = f"{filename}.json"

            return data, filename, mimetype

        elif format == 'csv':
            # CSV export is more complex as we need separate files for different data types
            # Let's create a zip file containing multiple CSVs
            import zipfile

            # Create a BytesIO object to hold the zip file
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add goals CSV
                goals_csv = ImportExportService._goals_to_csv(goals)
                zipf.writestr('goals.csv', goals_csv)

                # Add tasks CSV
                tasks_csv = ImportExportService._tasks_to_csv(tasks)
                zipf.writestr('tasks.csv', tasks_csv)

                # Add metadata JSON
                metadata = {
                    'exported_at': datetime.now().isoformat(),
                    'username': user.username,
                    'app_version': '1.0',
                }
                zipf.writestr('metadata.json', json.dumps(metadata, indent=2))

            zip_buffer.seek(0)
            data = zip_buffer.getvalue()
            mimetype = 'application/zip'
            filename = f"{filename}.zip"

            return data, filename, mimetype

        else:
            # Unsupported format
            return None, None, None

    @staticmethod
    def import_data(user_id, file_data, filename):
        """
        Import user data from a file.

        Args:
            user_id: The ID of the user to import data for
            file_data: The uploaded file data
            filename: The original filename

        Returns:
            dict: Results of the import operation
        """
        # Determine file type from extension
        import_type = None
        if filename.endswith('.json'):
            import_type = 'json'
        elif filename.endswith('.zip'):
            import_type = 'csv'
        else:
            return {'success': False, 'message': 'Unsupported file type. Please upload a .json or .zip file.'}

        try:
            if import_type == 'json':
                # Parse JSON data
                data = json.loads(file_data)
                return ImportExportService._import_from_json(user_id, data)

            elif import_type == 'csv':
                # Handle ZIP file with CSVs
                import zipfile
                import io

                zip_buffer = io.BytesIO(file_data)
                with zipfile.ZipFile(zip_buffer, 'r') as zipf:
                    # Check for required files
                    required_files = ['goals.csv', 'tasks.csv']
                    missing_files = [f for f in required_files if f not in zipf.namelist()]

                    if missing_files:
                        return {'success': False, 'message': f'Invalid export file. Missing: {", ".join(missing_files)}'}

                    # Read the files
                    goals_csv = zipf.read('goals.csv').decode('utf-8')
                    tasks_csv = zipf.read('tasks.csv').decode('utf-8')

                    return ImportExportService._import_from_csv(user_id, goals_csv, tasks_csv)

        except Exception as e:
            current_app.logger.error(f"Import error: {str(e)}")
            return {'success': False, 'message': f'Error importing data: {str(e)}'}

    @staticmethod
    def _serialize_goal(goal):
        """Convert a goal to a dictionary for export."""
        data = {
            'id': goal.id,
            'title': goal.title,
            'description': goal.description,
            'start_date': goal.start_date.isoformat() if goal.start_date else None,
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'progress': goal.progress,
            'is_completed': goal.is_completed,
            'type': goal.type,
            'created_at': goal.created_at.isoformat(),
            'updated_at': goal.updated_at.isoformat(),
            # Store the IDs of related entities for rebuilding relationships
            'parent_goal_ids': [g.id for g in goal.parent_goals],
            'related_task_ids': [t.id for t in goal.related_tasks],
        }

        # Add type-specific fields
        if goal.type == 'long_term':
            data['timeframe'] = goal.timeframe
        elif goal.type == 'short_term' or goal.type == 'milestone':
            data['priority'] = goal.priority
            data['difficulty'] = goal.difficulty
            data['estimated_effort'] = goal.estimated_effort

            if goal.type == 'milestone':
                data['parent_long_term_goal_id'] = goal.parent_long_term_goal_id
                data['sequence'] = goal.sequence
                data['is_gateway'] = goal.is_gateway

        return data

    @staticmethod
    def _serialize_task(task):
        """Convert a task to a dictionary for export."""
        data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'priority': task.priority,
            'is_completed': task.is_completed,
            'estimated_duration': task.estimated_duration,
            'actual_duration': task.actual_duration,
            'type': task.type,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            # Store the IDs of related entities for rebuilding relationships
            'related_goal_ids': [g.id for g in task.related_goals],
        }

        # Add type-specific fields
        if task.type == 'one_time':
            data['deadline'] = task.deadline.isoformat() if task.deadline else None
            data['reminder'] = task.reminder.isoformat() if task.reminder else None
        elif task.type == 'recurring':
            data['frequency'] = task.frequency
            data['interval'] = task.interval
            data['end_date'] = task.end_date.isoformat() if task.end_date else None

        return data

    @staticmethod
    def _goals_to_csv(goals):
        """Convert goals to CSV format."""
        output = io.StringIO()

        # Define fields for CSV
        fieldnames = [
            'id', 'title', 'description', 'start_date', 'target_date',
            'progress', 'is_completed', 'type', 'created_at', 'updated_at',
            'timeframe', 'priority', 'difficulty', 'estimated_effort',
            'parent_long_term_goal_id', 'sequence', 'is_gateway',
            'parent_goal_ids', 'related_task_ids'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for goal in goals:
            # Start with serialized goal
            row = ImportExportService._serialize_goal(goal)

            # Convert list fields to comma-separated strings
            row['parent_goal_ids'] = ','.join(str(x) for x in row['parent_goal_ids'])
            row['related_task_ids'] = ','.join(str(x) for x in row['related_task_ids'])

            # Ensure all fields are in the row
            for field in fieldnames:
                if field not in row:
                    row[field] = None

            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def _tasks_to_csv(tasks):
        """Convert tasks to CSV format."""
        output = io.StringIO()

        # Define fields for CSV
        fieldnames = [
            'id', 'title', 'description', 'due_date', 'priority',
            'is_completed', 'estimated_duration', 'actual_duration',
            'type', 'created_at', 'updated_at', 'deadline', 'reminder',
            'frequency', 'interval', 'end_date', 'related_goal_ids'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for task in tasks:
            # Start with serialized task
            row = ImportExportService._serialize_task(task)

            # Convert list fields to comma-separated strings
            row['related_goal_ids'] = ','.join(str(x) for x in row['related_goal_ids'])

            # Ensure all fields are in the row
            for field in fieldnames:
                if field not in row:
                    row[field] = None

            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def _import_from_json(user_id, data):
        """Import data from a JSON structure."""
        try:
            # Validate the data structure
            required_keys = ['metadata', 'goals', 'tasks']
            for key in required_keys:
                if key not in data:
                    return {'success': False, 'message': f'Invalid export file. Missing "{key}" section.'}

            # Begin the import transaction
            # First, create a mapping of old goal IDs to new goal objects
            goal_map = {}
            task_map = {}

            # Create all goals first
            for goal_data in data['goals']:
                # Check if this goal type is valid
                if goal_data['type'] not in ['long_term', 'short_term', 'milestone', 'goal']:
                    continue

                # Create the appropriate goal object
                if goal_data['type'] == 'long_term':
                    goal = LongTermGoal(user_id=user_id)
                elif goal_data['type'] == 'milestone':
                    goal = MilestoneGoal(user_id=user_id)
                elif goal_data['type'] == 'short_term':
                    goal = ShortTermGoal(user_id=user_id)
                else:
                    goal = Goal(user_id=user_id)

                # Set basic fields
                ImportExportService._set_goal_fields(goal, goal_data)

                # Save the goal to get an ID
                db.session.add(goal)

                # Add to the mapping
                goal_map[goal_data['id']] = goal

            # Create all tasks next
            for task_data in data['tasks']:
                # Check if this task type is valid
                if task_data['type'] not in ['one_time', 'recurring', 'task']:
                    continue

                # Create the appropriate task object
                if task_data['type'] == 'one_time':
                    task = OneTimeTask(user_id=user_id)
                elif task_data['type'] == 'recurring':
                    task = RecurringTask(user_id=user_id)
                else:
                    task = Task(user_id=user_id)

                # Set basic fields
                ImportExportService._set_task_fields(task, task_data)

                # Save the task to get an ID
                db.session.add(task)

                # Add to the mapping
                task_map[task_data['id']] = task

            # Commit to save all objects
            db.session.commit()

            # Now establish relationships
            # For goals: parent-child relationships
            for goal_data in data['goals']:
                if 'parent_goal_ids' in goal_data and goal_data['id'] in goal_map:
                    goal = goal_map[goal_data['id']]
                    for parent_id in goal_data['parent_goal_ids']:
                        if parent_id in goal_map:
                            parent_goal = goal_map[parent_id]
                            goal.link_to_goal(parent_goal)

            # For tasks: link to goals
            for task_data in data['tasks']:
                if 'related_goal_ids' in task_data and task_data['id'] in task_map:
                    task = task_map[task_data['id']]
                    for goal_id in task_data['related_goal_ids']:
                        if goal_id in goal_map:
                            goal = goal_map[goal_id]
                            task.link_to_goal(goal)

            # Final commit to save relationships
            db.session.commit()

            return {
                'success': True,
                'message': f'Successfully imported {len(goal_map)} goals and {len(task_map)} tasks.',
                'goal_count': len(goal_map),
                'task_count': len(task_map)
            }

        except Exception as e:
            # Roll back in case of error
            db.session.rollback()
            current_app.logger.error(f"Import error: {str(e)}")
            return {'success': False, 'message': f'Error importing data: {str(e)}'}

    @staticmethod
    def _import_from_csv(user_id, goals_csv, tasks_csv):
        """Import data from CSV files."""
        try:
            # Parse the CSVs
            goals_data = list(csv.DictReader(io.StringIO(goals_csv)))
            tasks_data = list(csv.DictReader(io.StringIO(tasks_csv)))

            # Convert to the format expected by _import_from_json
            json_data = {
                'metadata': {
                    'imported_at': datetime.now().isoformat(),
                },
                'goals': [],
                'tasks': []
            }

            # Process goals
            for row in goals_data:
                goal_data = dict(row)

                # Convert string representations to appropriate types
                if goal_data['progress']:
                    goal_data['progress'] = float(goal_data['progress'])

                if goal_data['is_completed']:
                    goal_data['is_completed'] = goal_data['is_completed'].lower() == 'true'

                if goal_data['difficulty'] and goal_data['difficulty'] != 'None':
                    goal_data['difficulty'] = float(goal_data['difficulty'])

                if goal_data['estimated_effort'] and goal_data['estimated_effort'] != 'None':
                    goal_data['estimated_effort'] = float(goal_data['estimated_effort'])

                if goal_data['is_gateway']:
                    goal_data['is_gateway'] = goal_data['is_gateway'].lower() == 'true'

                # Process relationship fields
                if goal_data['parent_goal_ids']:
                    goal_data['parent_goal_ids'] = [int(x) for x in goal_data['parent_goal_ids'].split(',') if x]
                else:
                    goal_data['parent_goal_ids'] = []

                if goal_data['related_task_ids']:
                    goal_data['related_task_ids'] = [int(x) for x in goal_data['related_task_ids'].split(',') if x]
                else:
                    goal_data['related_task_ids'] = []

                json_data['goals'].append(goal_data)

            # Process tasks
            for row in tasks_data:
                task_data = dict(row)

                # Convert string representations to appropriate types
                if task_data['is_completed']:
                    task_data['is_completed'] = task_data['is_completed'].lower() == 'true'

                if task_data['estimated_duration'] and task_data['estimated_duration'] != 'None':
                    task_data['estimated_duration'] = float(task_data['estimated_duration'])

                if task_data['actual_duration'] and task_data['actual_duration'] != 'None':
                    task_data['actual_duration'] = float(task_data['actual_duration'])

                if task_data['interval'] and task_data['interval'] != 'None':
                    task_data['interval'] = int(task_data['interval'])

                # Process relationship fields
                if task_data['related_goal_ids']:
                    task_data['related_goal_ids'] = [int(x) for x in task_data['related_goal_ids'].split(',') if x]
                else:
                    task_data['related_goal_ids'] = []

                json_data['tasks'].append(task_data)

            # Use the JSON import function
            return ImportExportService._import_from_json(user_id, json_data)

        except Exception as e:
            current_app.logger.error(f"CSV import error: {str(e)}")
            return {'success': False, 'message': f'Error importing CSV data: {str(e)}'}

    @staticmethod
    def _set_goal_fields(goal, data):
        """Set the fields on a goal object from the data dictionary."""
        # Basic fields
        goal.title = data['title']
        goal.description = data['description']

        # Handle date fields
        if data['start_date']:
            goal.start_date = datetime.fromisoformat(data['start_date'])

        if data['target_date']:
            goal.target_date = datetime.fromisoformat(data['target_date'])

        goal.progress = data['progress']
        goal.is_completed = data['is_completed']

        # Type-specific fields
        if goal.type == 'long_term' and 'timeframe' in data:
            goal.timeframe = data['timeframe']

        if (goal.type == 'short_term' or goal.type == 'milestone'):
            if 'priority' in data:
                goal.priority = data['priority']

            if 'difficulty' in data and data['difficulty'] is not None:
                goal.difficulty = data['difficulty']

            if 'estimated_effort' in data and data['estimated_effort'] is not None:
                goal.estimated_effort = data['estimated_effort']

        if goal.type == 'milestone':
            if 'parent_long_term_goal_id' in data and data['parent_long_term_goal_id']:
                goal.parent_long_term_goal_id = data['parent_long_term_goal_id']

            if 'sequence' in data and data['sequence']:
                goal.sequence = data['sequence']

            if 'is_gateway' in data:
                goal.is_gateway = data['is_gateway']

    @staticmethod
    def _set_task_fields(task, data):
        """Set the fields on a task object from the data dictionary."""
        # Basic fields
        task.title = data['title']
        task.description = data['description']

        # Handle date fields
        if data['due_date']:
            task.due_date = datetime.fromisoformat(data['due_date'])

        task.priority = data['priority']
        task.is_completed = data['is_completed']

        if data['estimated_duration'] is not None:
            task.estimated_duration = data['estimated_duration']

        if data['actual_duration'] is not None:
            task.actual_duration = data['actual_duration']

        # Type-specific fields
        if task.type == 'one_time':
            if data['deadline']:
                task.deadline = datetime.fromisoformat(data['deadline'])

            if data['reminder']:
                task.reminder = datetime.fromisoformat(data['reminder'])

        if task.type == 'recurring':
            if 'frequency' in data:
                task.frequency = data['frequency']

            if 'interval' in data and data['interval'] is not None:
                task.interval = data['interval']

            if data['end_date']:
                task.end_date = datetime.fromisoformat(data['end_date'])
