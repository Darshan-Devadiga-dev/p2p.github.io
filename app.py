from flask import Flask, request, send_file, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pairdrop-clone'
app.config['UPLOAD_FOLDER'] = 'uploads'

socketio = SocketIO(app, cors_allowed_origins="*")
peers = {}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return 'Backend is running.'

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/upload', methods=['POST'])
def upload():
    peer_id = request.form.get("peer_id")
    file = request.files.get("file")
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        # Notify the recipient peer
        socketio.emit('file-received', {
            'filename': filename,
            'sender': peer_id,
            'download_url': f"/download/{filename}"
        }, broadcast=True)

        return jsonify({"status": "success", "filename": filename})
    return jsonify({"status": "error", "message": "No file received"}), 400

@socketio.on('connect')
def on_connect():
    print(f"Client connected: {request.sid}")
    peers[request.sid] = {"id": request.sid}
    emit('peer-list', list(peers.values()), broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in peers:
        del peers[request.sid]
    emit('peer-list', list(peers.values()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
