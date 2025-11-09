from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from utils.thumbnail_generator import ThumbnailGenerator
import logging
import subprocess
import threading
import atexit

app = Flask(__name__, static_folder='assets', template_folder='pages')
CORS(app)

UPLOAD_ROOT = 'data/notes'
NOTES_JSON = 'data/notes-data.json'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store watcher process
watcher_process = None

def start_file_watcher():
    """Start the file watcher in a separate process"""
    global watcher_process
    try:
        watcher_script = os.path.join('scripts', 'auto-update-watcher.js')
        watcher_process = subprocess.Popen(['node', watcher_script], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
        logger.info("File watcher started successfully")
    except Exception as e:
        logger.error(f"Failed to start file watcher: {str(e)}")

def stop_file_watcher():
    """Stop the file watcher process"""
    global watcher_process
    if watcher_process:
        watcher_process.terminate()
        watcher_process.wait()
        logger.info("File watcher stopped")

# Register cleanup function
atexit.register(stop_file_watcher)

@app.route('/')
def home():
    """Serve homepage (index.html)"""
    return send_from_directory('.', 'index.html')

@app.route('/api/admin/upload', methods=['POST'])
def admin_upload():
    semester_id = request.form.get('semester')
    branch_id = request.form.get('branch')
    subject_id = request.form.get('subject')
    title = request.form.get('title')
    description = request.form.get('description')
    pdf = request.files.get('pdf')

    if not all([semester_id, branch_id, subject_id, title, description, pdf]):
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    # Load notes-data.json
    with open(NOTES_JSON, 'r', encoding='utf-8') as f:
        notes_data = json.load(f)

    # Find semester, branch, subject
    semester = next((s for s in notes_data['semesters'] if str(s['id']) == str(semester_id)), None)
    if not semester:
        return jsonify({'success': False, 'message': 'Semester not found.'}), 404
    branch = next((b for b in semester['branches'] if b['id'] == branch_id), None)
    if not branch:
        return jsonify({'success': False, 'message': 'Branch not found.'}), 404
    subject = next((sub for sub in branch['subjects'] if sub['id'] == subject_id), None)
    if not subject:
        return jsonify({'success': False, 'message': 'Subject not found.'}), 404

    # Save PDF
    safe_filename = secure_filename(pdf.filename)
    folder_path = os.path.join(UPLOAD_ROOT, f'semester-{semester_id}', branch_id, subject['name'].replace(' ', '-').lower())
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, safe_filename)
    pdf.save(file_path)

    # Generate thumbnail asynchronously in background
    try:
        success, message = ThumbnailGenerator.generate_thumbnail(file_path, output_format='png')
        if success:
            logger.info(f"Thumbnail generated for {file_path}: {message}")
        else:
            logger.warning(f"Failed to generate thumbnail for {file_path}: {message}")
            # Don't fail the upload if thumbnail generation fails
    except Exception as e:
        logger.error(f"Error generating thumbnail for {file_path}: {str(e)}")

    # Update JSON
    rel_path = '/' + file_path.replace('\\', '/').replace(os.path.sep, '/')
    thumbnail_url = ThumbnailGenerator.get_thumbnail_url(file_path, format='png')
    
    material = {
        'title': title,
        'description': description,
        'path': rel_path,
        'type': 'pdf',
        'size': f"{os.path.getsize(file_path) // 1024}KB",
        'uploadDate': datetime.now().strftime('%Y-%m-%d'),
        'downloadUrl': f"/api/download?path={rel_path}",
        'thumbnailUrl': thumbnail_url
    }
    subject.setdefault('materials', []).append(material)

    with open(NOTES_JSON, 'w', encoding='utf-8') as f:
        json.dump(notes_data, f, indent=2, ensure_ascii=False)

    return jsonify({'success': True, 'message': 'PDF uploaded and notes updated.', 'thumbnailUrl': thumbnail_url})

@app.route('/api/download')
def download():
    path = request.args.get('path')
    if not path or not os.path.isfile(path.lstrip('/')):
        return 'File not found', 404
    dir_name = os.path.dirname(path.lstrip('/'))
    file_name = os.path.basename(path)
    return send_from_directory(dir_name, file_name, as_attachment=True)

@app.route('/api/thumbnail')
def get_thumbnail():
    """
    Serve PDF thumbnails
    Query Parameters:
        path: Path to the PDF file
        format: Thumbnail format ('png' or 'webp', default: 'png')
    """
    pdf_path = request.args.get('path')
    output_format = request.args.get('format', 'png').lower()
    
    if not pdf_path:
        return jsonify({'success': False, 'message': 'Missing path parameter'}), 400
    
    if output_format not in ['png', 'webp']:
        output_format = 'png'
    
    # Ensure thumbnails directory exists
    ThumbnailGenerator.ensure_thumbnails_dir()
    
    # Get thumbnail path
    thumbnail_path = ThumbnailGenerator.get_thumbnail_path(pdf_path, output_format)
    
    # Check if thumbnail exists; if not, generate it
    if not os.path.exists(thumbnail_path):
        # Check if PDF exists
        pdf_file_path = pdf_path.lstrip('/')
        if not os.path.isfile(pdf_file_path):
            return jsonify({'success': False, 'message': 'PDF file not found'}), 404
        
        # Generate thumbnail
        success, message = ThumbnailGenerator.generate_thumbnail(pdf_file_path, output_format)
        if not success:
            return jsonify({'success': False, 'message': message}), 500
    
    # Serve the thumbnail
    try:
        return send_from_directory(os.path.dirname(thumbnail_path), os.path.basename(thumbnail_path))
    except Exception as e:
        logger.error(f"Error serving thumbnail {thumbnail_path}: {str(e)}")
        return jsonify({'success': False, 'message': 'Error serving thumbnail'}), 500

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('pages', filename)

@app.route('/api/admin/delete-material', methods=['POST'])
def delete_material():
    """
    Delete a material (PDF) and its associated thumbnail
    """
    data = request.get_json()
    semester_id = data.get('semester')
    branch_id = data.get('branch')
    subject_id = data.get('subject')
    material_path = data.get('path')
    
    if not all([semester_id, branch_id, subject_id, material_path]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    try:
        # Load notes-data.json
        with open(NOTES_JSON, 'r', encoding='utf-8') as f:
            notes_data = json.load(f)
        
        # Find and remove material
        semester = next((s for s in notes_data['semesters'] if str(s['id']) == str(semester_id)), None)
        if not semester:
            return jsonify({'success': False, 'message': 'Semester not found'}), 404
        
        branch = next((b for b in semester['branches'] if b['id'] == branch_id), None)
        if not branch:
            return jsonify({'success': False, 'message': 'Branch not found'}), 404
        
        subject = next((sub for sub in branch['subjects'] if sub['id'] == subject_id), None)
        if not subject:
            return jsonify({'success': False, 'message': 'Subject not found'}), 404
        
        # Remove material from list
        original_count = len(subject.get('materials', []))
        subject['materials'] = [m for m in subject.get('materials', []) if m['path'] != material_path]
        
        if len(subject['materials']) == original_count:
            return jsonify({'success': False, 'message': 'Material not found'}), 404
        
        # Delete PDF file
        pdf_file_path = material_path.lstrip('/')
        if os.path.exists(pdf_file_path):
            os.remove(pdf_file_path)
            logger.info(f"PDF file deleted: {pdf_file_path}")
        
        # Delete thumbnail
        success = ThumbnailGenerator.delete_thumbnail(pdf_file_path)
        if success:
            logger.info(f"Thumbnail deleted for: {pdf_file_path}")
        
        # Update JSON
        with open(NOTES_JSON, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Material and thumbnail deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting material: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)

if __name__ == '__main__':
    # Start file watcher
    start_file_watcher()
    
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        stop_file_watcher()
