from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://cute-monstera-6eef17.netlify.app"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

app.config['SECRET_KEY'] = 'pairdrop-clone'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# IMPORTANT: Use 'threading' to avoid file upload issues
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

peers = {}

@app.route('/')
def home():
    return 'PairDrop backend running.'

@app.route('/upload', methods=['POST'])
def upload():
    peer_id = request.form.get("peer_id")
    file = request.files.get("file")

    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # Notify all peers except sender
        socketio.emit('file-received', {
            'filename': filename,
            'sender': peer_id,
            'download_url': f"/download/{filename}"
        }, broadcast=True)

        return jsonify({"status": "success", "filename": filename})
    else:
        return jsonify({"status": "error", "message": "No file received"}), 400

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    peers[sid] = {'id': sid}
    print(f"Connected: {sid}")
    emit('peer-list', list(peers.values()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f"Disconnected: {sid}")
    peers.pop(sid, None)
    emit('peer-list', list(peers.values()), broadcast=True)

# ✔️ FINAL FIX: allow_unsafe_werkzeug added
if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
