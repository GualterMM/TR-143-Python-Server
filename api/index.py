from flask import Flask, request, send_file, Response
import os
import time
from datetime import datetime
# import threading
import tempfile

app = Flask(__name__)

# Store test files and results
test_files = {}
test_results = {}

def create_test_file(size_bytes):
    """Create a test file of specified size filled with random data"""
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'wb') as f:
        f.write(os.urandom(size_bytes))
    return path

@app.route('/download', methods=['GET'])
def download_test():
    """TR-143 Download Diagnostic"""
    size = int(request.args.get('size', 1000000))  # Default 1MB
    test_id = request.args.get('testid', datetime.now().isoformat())
    
    if test_id not in test_files:
        test_files[test_id] = create_test_file(size)
    
    # Record start time
    test_results[test_id] = {
        'start_time': time.time(),
        'size': size
    }
    
    return send_file(
        test_files[test_id],
        as_attachment=True,
        download_name=f'speedtest_{test_id}.bin'
    )

@app.route('/upload', methods=['POST'])
def upload_test():
    """TR-143 Upload Diagnostic"""
    test_id = request.args.get('testid', datetime.now().isoformat())
    
    # Record start time and size
    test_results[test_id] = {
        'start_time': time.time(),
        'size': request.content_length
    }
    
    # Consume the upload data
    request.get_data()
    
    # Calculate duration and speed
    duration = time.time() - test_results[test_id]['start_time']
    speed_bps = (test_results[test_id]['size'] * 8) / duration
    
    return {
        'testid': test_id,
        'duration_seconds': duration,
        'bytes_transferred': test_results[test_id]['size'],
        'speed_bps': speed_bps
    }

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up test files"""
    test_id = request.args.get('testid')
    if test_id in test_files:
        os.remove(test_files[test_id])
        del test_files[test_id]
        del test_results[test_id]
    return {'status': 'cleaned'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)