from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import uuid
import shutil
from werkzeug.utils import secure_filename
from utils.stego_core import SteganographyAES
import traceback
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
STATIC_FOLDER = 'static'
COMPARISON_FOLDER = 'static/comparisons'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
ALLOWED_FILE_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(COMPARISON_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(filename):
    """Generate unique filename to avoid conflicts"""
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(filename)
    return f"{name}_{unique_id}{ext}"

def copy_image_for_comparison(source_path, comparison_id, image_type):
    """Copy image to static folder for web display"""
    filename = f"{comparison_id}_{image_type}.png"
    destination = os.path.join(COMPARISON_FOLDER, filename)
    shutil.copy2(source_path, destination)
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract')
def extract_page():
    return render_template('extract.html')

@app.route('/hide', methods=['POST'])
def hide_data():
    try:
        # Validate inputs
        if 'cover_image' not in request.files:
            flash('Cover image is required!', 'error')
            return redirect(url_for('index'))
        
        cover_file = request.files['cover_image']
        password = request.form.get('password', '').strip()
        input_method = request.form.get('input_method', 'text')
        
        if cover_file.filename == '':
            flash('No cover image selected!', 'error')
            return redirect(url_for('index'))
        
        if not password:
            flash('Password is required!', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(cover_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            flash('Invalid image format! Allowed: PNG, JPG, JPEG, GIF, BMP', 'error')
            return redirect(url_for('index'))
        
        # Save cover image
        cover_filename = secure_filename(cover_file.filename)
        cover_filename = generate_unique_filename(cover_filename)
        cover_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_filename)
        cover_file.save(cover_path)
        
        # Generate output filename (force PNG)
        output_filename = f"stego_{os.path.splitext(cover_filename)[0]}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Create steganography instance
        stego_system = SteganographyAES(password)
        
        if input_method == 'text':
            # Text input method
            secret_text = request.form.get('secret_text', '').strip()
            if not secret_text:
                flash('Secret text is required!', 'error')
                return redirect(url_for('index'))
            
            result_path = stego_system.hide_message_from_text(cover_path, secret_text, output_path)
            data_info = {
                'type': 'text',
                'content_length': len(secret_text),
                'original_name': 'user_input.txt'
            }
            
        elif input_method == 'file':
            # File input method
            if 'secret_file' not in request.files:
                flash('Secret file is required!', 'error')
                return redirect(url_for('index'))
            
            secret_file = request.files['secret_file']
            if secret_file.filename == '':
                flash('No secret file selected!', 'error')
                return redirect(url_for('index'))
            
            if not allowed_file(secret_file.filename, ALLOWED_FILE_EXTENSIONS):
                flash('Invalid file format! Allowed: TXT, PDF, DOC, DOCX, XLSX, XLS', 'error')
                return redirect(url_for('index'))
            
            # Save secret file
            secret_filename = secure_filename(secret_file.filename)
            secret_filename = generate_unique_filename(secret_filename)
            secret_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_filename)
            secret_file.save(secret_path)
            
            result_path = stego_system.hide_message_from_file(cover_path, secret_path, output_path)
            data_info = {
                'type': 'file',
                'original_name': secret_file.filename,
                'file_size': os.path.getsize(secret_path)
            }
            
            # Clean up secret file
            os.remove(secret_path)
        
        else:
            flash('Invalid input method!', 'error')
            return redirect(url_for('index'))
        
        # Analyze image quality
        try:
            mse, psnr = stego_system.analyze_image_quality(cover_path, output_path)
            quality_info = {'mse': mse, 'psnr': psnr}
        except Exception as e:
            quality_info = {'mse': 'N/A', 'psnr': 'N/A', 'error': str(e)}
        
        # Create comparison images for web display
        comparison_id = str(uuid.uuid4())[:8]
        original_image = copy_image_for_comparison(cover_path, comparison_id, 'original')
        stego_image = copy_image_for_comparison(output_path, comparison_id, 'stego')
        
        comparison_info = {
            'original_image': original_image,
            'stego_image': stego_image,
            'original_filename': cover_file.filename,
            'stego_filename': output_filename
        }
        
        # Clean up cover image from uploads
        os.remove(cover_path)
        
        return render_template('result.html',
                             action='hide',
                             output_file=output_filename,
                             data_info=data_info,
                             quality_info=quality_info,
                             comparison_info=comparison_info)
    
    except Exception as e:
        app.logger.error(f"Error in hide_data: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/extract_data', methods=['POST'])
def extract_data():
    try:
        # Validate inputs
        if 'stego_image' not in request.files:
            flash('Steganographic image is required!', 'error')
            return redirect(url_for('extract_page'))
        
        stego_file = request.files['stego_image']
        password = request.form.get('password', '').strip()
        
        if stego_file.filename == '':
            flash('No steganographic image selected!', 'error')
            return redirect(url_for('extract_page'))
        
        if not password:
            flash('Password is required!', 'error')
            return redirect(url_for('extract_page'))
        
        if not allowed_file(stego_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            flash('Invalid image format! Allowed: PNG, JPG, JPEG, GIF, BMP', 'error')
            return redirect(url_for('extract_page'))
        
        # Save steganographic image
        stego_filename = secure_filename(stego_file.filename)
        stego_filename = generate_unique_filename(stego_filename)
        stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
        stego_file.save(stego_path)
        
        # Create steganography instance
        stego_system = SteganographyAES(password)
        
        # Extract data
        extracted_content, metadata = stego_system.extract_message(stego_path)
        
        # Create downloadable file
        output_file = stego_system.create_downloadable_file(extracted_content, metadata)
        output_filename = os.path.basename(output_file)
        
        # Move file to outputs folder
        final_output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        os.rename(output_file, final_output_path)
        
        # Clean up steganographic image
        os.remove(stego_path)
        
        return render_template('result.html',
                             action='extract',
                             output_file=output_filename,
                             metadata=metadata,
                             extracted_content=extracted_content if metadata.get('type') == 'text' else None)
    
    except Exception as e:
        app.logger.error(f"Error in extract_data: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('extract_page'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            flash('File not found!', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Steganography Web App is running'})

@app.errorhandler(413)
def too_large(e):
    flash('File too large! Maximum file size is 16MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)