from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import subprocess
import logging
from datetime import datetime
import jwt
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-here')  # Change in production

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            # You can add user data to request here
            # request.user = get_user(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/upload', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Generate unique filename
        filename = str(uuid.uuid4()) + '.mp4'
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(PROCESSED_FOLDER, f"{filename.split('.')[0]}_processed.mp4")
        
        logger.info(f"Saving uploaded file to: {input_path}")
        file.save(input_path)
        
        logger.info(f"Processing video: {input_path} -> {output_path}")
        command = [
            'ntsc-rs-cli',
            '--input', input_path,
            '--output', output_path,
            '--overwrite'
        ]
        
        # Run the command and capture output
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Video processing completed successfully")
            
            # Send the processed file
            logger.info(f"Sending processed file: {output_path}")
            return send_file(output_path, as_attachment=True)
        else:
            logger.error(f"Video processing failed: {result.stderr}")
            return jsonify({'error': 'Video processing failed'}), 500
            
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Cleanup files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

@app.route('/auth', methods=['POST'])
@limiter.limit("5 per minute")
def authenticate():
    # This is a simple authentication endpoint
    # In production, you should validate against a user database
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Authentication required'}), 401
    
    # Demo authentication - replace with actual user validation
    if auth.username == "demo" and auth.password == "password":
        token = jwt.encode({
            'user': auth.username,
            'exp': datetime.utcnow().timestamp() + 86400  # 24 hour expiration
        }, JWT_SECRET)
        
        return jsonify({
            'token': token,
            'expires_in': 86400
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
