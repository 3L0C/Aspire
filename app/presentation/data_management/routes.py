#!/usr/bin/env python3

from flask import render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.presentation.data_management import data_management
from app.services.import_export_service import ImportExportService
import io

@data_management.route('/')
@login_required
def index():
    """Import/Export page."""
    return render_template('data_management/index.html', title='Import/Export Data')

@data_management.route('/export', methods=['POST'])
@login_required
def export_data():
    """Export user data."""
    format = request.form.get('format', 'json')

    # Get export data
    data, filename, mimetype = ImportExportService.export_data(current_user.id, format)

    if not data:
        flash('Error exporting data.', 'danger')
        return redirect(url_for('data_management.index'))

    # Send file to user
    return send_file(
        io.BytesIO(data.encode() if isinstance(data, str) else data),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

@data_management.route('/import', methods=['POST'])
@login_required
def import_data():
    """Import user data."""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('data_management.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('data_management.index'))

    if file:
        # Read the file
        file_data = file.read()

        # Import the data
        result = ImportExportService.import_data(current_user.id, file_data, file.filename)

        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'danger')

        return redirect(url_for('data_management.index'))

    flash('Error importing data.', 'danger')
    return redirect(url_for('data_management.index'))
