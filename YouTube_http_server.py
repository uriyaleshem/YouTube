from flask import Flask, Response, request
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

VIDEO_DIR = "youtube"

@app.route('/video/<title>')
def stream_video(title):
    file_path = os.path.join(VIDEO_DIR, title)
    if not os.path.exists(file_path):
        return "Video not found", 404

    size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)
    byte1, byte2 = 0, size - 1
    range_header = request.headers.get('Range', None)
    print(" Range Header:", range_header)

    if range_header:
        match = range_header.strip().split('=')[-1]
        if '-' in match:
            parts = match.split('-')
            if parts[0]:
                byte1 = int(parts[0])
            if len(parts) > 1 and parts[1]:
                byte2 = int(parts[1]) if parts[1] else size - 1

    length = byte2 - byte1 + 1

    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    resp = Response(data, status=206 if range_header else 200, mimetype='video/mp4', direct_passthrough=True)
    resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{size}')
    resp.headers.add('Accept-Ranges', 'bytes')
    resp.headers.add('Content-Length', str(length))
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
